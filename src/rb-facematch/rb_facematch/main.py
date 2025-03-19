import json
import os
import sys
from pathlib import Path
import logging
from typing import Annotated, Any, List, TypedDict
from fastapi import Body, Depends, HTTPException, Response
from pydantic import DirectoryPath, Field, PositiveFloat, StrictStr
from rb.api.models import (
    FileInput,
    DirectoryInput,
    BatchDirectoryInput,
    FileResponse,
    BatchFileInput,
    BatchFileResponse,
    EnumParameterDescriptor,
    EnumVal,
    FloatRangeDescriptor,
    TextParameterDescriptor,
    TextResponse,
)
from rb.api.models import (
    API_APPMETDATA,
    API_ROUTES,
    PLUGIN_SCHEMA_SUFFIX,
    InputSchema,
    InputType,
    ParameterSchema,
    RangedFloatParameterDescriptor,
    ResponseBody,
    TaskSchema,
)
import typer
from rb_facematch.src.facematch.interface import FaceMatchModel
from rb_facematch.src.facematch.utils.GPU import check_cuDNN_version
from rb.api.utils import string_to_dict

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = typer.Typer()

# create an instance of the model
face_match_model = FaceMatchModel()

info_file_path = Path("app-info.md")


def load_file_as_string(file_path: str) -> str:
    """read in plugin doc"""

    target = Path(__file__).parent.resolve()
    # pyinstaller exe path
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        temp = getattr(sys, "_MEIPASS", Path(__file__).resolve())
        target = Path(temp) / "audio"

    full_path = target / Path(file_path)

    if not full_path.is_file():
        raise FileNotFoundError(f"File {full_path} not found")
    with open(full_path, "r") as f:
        return f.read()


@app.command(API_APPMETDATA)  # ("/api/app_metadata") Electron call
def app_metadata() -> Any:
    obj = {
        "name": "Facematch",
        "author": "UMass Rescue",
        "version": "0.1.0",
        "info": load_file_as_string(info_file_path),
    }
    return obj


@app.command(API_ROUTES)  # /api/routes Electron call
def routes() -> Any:
    route = [
        {
            "task_schema": "/facematch/upload_schema",
            "run_task": "/facematch/bulkupload",
            "short_title": "Upload Images to Database",
            "order": 0,
        },
        {
            "task_schema": "/facematch/find_face_task_schema",
            "run_task": "/facematch/findface",
            "short_title": "Find Matching Faces",
            "order": 1,
        },
    ]
    routes_list = [
        route,
    ]
    return routes_list


available_databases: List[str] = ["Create a new database"]
default_threshold = 0.45


@app.command(f"find_face_task{PLUGIN_SCHEMA_SUFFIX}")
def find_face_task_schema() -> Response:
    """matching route order=1"""
    obj = TaskSchema(
        inputs=[
            InputSchema(
                key="image_paths",
                label="Image Path",
                input_type=InputType.BATCHFILE,
            )
        ],
        parameters=[
            ParameterSchema(
                key="database_name",
                label="Database Name",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=database_name, label=database_name)
                        for database_name in available_databases[0:]
                    ],
                    message_when_empty="No databases found",
                    default=(available_databases[0]),
                ),
            ),
            ParameterSchema(
                key="similarity_threshold",
                label="Similarity Threshold",
                value=RangedFloatParameterDescriptor(
                    range=FloatRangeDescriptor(min=-1.0, max=1.0),
                    default=default_threshold,
                ),
            ),
        ],
    )
    return obj.model_dump(mode="json")


@app.command(f"upload{PLUGIN_SCHEMA_SUFFIX}")
def upload_task_schema() -> Response:
    """matching route order=0"""
    obj = TaskSchema(
        inputs=[
            InputSchema(
                key="directory_paths",
                label="Image Directory",
                input_type=InputType.BATCHDIRECTORY,
            )
        ],
        parameters=[
            ParameterSchema(
                key="dropdown_database_name",
                label="Choose Database",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=database_name, label=database_name)
                        for database_name in available_databases
                    ],
                    message_when_empty="No databases found",
                    default=(
                        available_databases[0] if len(available_databases) > 0 else ""
                    ),
                ),
            ),
            ParameterSchema(
                key="database_name",
                label="New Database Name (Optional)",
                value=TextParameterDescriptor(default="SampleDatabase"),
            ),
        ],
    )
    return obj.model_dump(mode="json")


class FindFaceInputs(TypedDict):
    """List of Files"""
    image_paths: BatchFileInput

class FindFaceParameters(TypedDict):
    """List of Files"""
    database_name: StrictStr
    similarity_threshold: PositiveFloat

def cli_inputs_parser(input_path: str) -> FindFaceInputs:
    """
    Mandatory cli callback
    input string value to pydantic type
    """
    try:
        logger.debug("-----DEBUG cli_inputs_parser inputs str to pydantic object ---")
        logger.debug(input_path)
        fileInput = FileInput(path=input_path)
        return BatchFileInput(files=List[fileInput])
    except Exception as e:
        logger.error(e)
        raise typer.Abort()


def validate_inputs(inputs: FindFaceInputs):
    """
    Optional verify inputs are usable callback
    note: fastapi only validates input is a pydantic object
    this fastapi Depends callback checks if files exists in directory
    """
    try:
        logger.debug("-----validate inputs ---")
        files = [file for file in inputs["image_paths"].files if file.path.is_file()]
        logger.debug(files)
        if len(files) < 1:
            raise HTTPException(
                status_code=400,
                detail="no files_in given directory for command",
            )
        logger.debug("------validate inputs done ---")
        ## this return object is now ready for use in function
        return inputs
    except Exception as e:
        logger.error("validate found bad inputs: %s", e)
        raise HTTPException(
            status_code=400, detail=f"Invalid path inputs for command: {e}"
        )


def cli_params_parser(p: str) -> FindFaceParameters:
    """
    Mandatory cli callback
    three parameters of type ; string/text , floar , int
    """
    try:
        params = string_to_dict(p)
        logger.debug("-----DEBUG FileParameters parser %s ---", params)
        if len(params) == 2:
            # check valid Input with pydantic types
            return FindFaceParameters(
                database_name= StrictStr(params[0]),
                similarity_threshold= PositiveFloat(params[1])
            )
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error("Invalid parameter input: %s", e)
        raise typer.Abort()


@app.command("findface")
def findface(
    inputs: Annotated[
        FindFaceInputs,
        typer.Argument(parser=cli_inputs_parser, help="input directory path"),
        Body(embed=True),
        Depends(validate_inputs),
    ],
    parameters: Annotated[
        FindFaceParameters,
        typer.Argument(parser=cli_params_parser, help="input params range and value "),
        Body(embed=True),
    ] = None, # type: ignore
) -> ResponseBody:
    ''' search for an image from the database'''
    # Get list of file paths from input
    input_file_paths = [item.path for item in inputs["image_paths"].files]

    # Convert database name to relative path to data directory in resources folder
    parameters["database_name"] = os.path.join(
        "data", parameters["database_name"] + ".csv"
    )
    logger.debug("--------")
    logger.debug(parameters)
    logger.debug(input_file_paths)
    logger.debug("--------")
                 
    # Check CUDNN compatability
    check_cuDNN_version()

    # Call model function to find matches
    status, results = face_match_model.find_face(
        input_file_paths[0],
        parameters["similarity_threshold"],
        parameters["database_name"],
    )
    # domain logic ...
    results = ["/foo", "/bar"]

    image_results = [
        FileResponse(file_type="img", path=res, title=res) for res in results
    ]
    logger.debug(image_results)

    return ResponseBody(root=BatchFileResponse(files=image_results))


# Inputs for the bulkupload endpoint
class BulkUploadInputs(TypedDict):
    """List of Directories with files to upload to a database"""
    directory_paths: BatchDirectoryInput

# Inputs for the bulkupload endpoint
class BulkUploadParameters(TypedDict):
    """Name of database to upload to"""
    dropdown_database_name: StrictStr = Field(max_length=64)
    database_name: StrictStr = Field(max_length=64)

def cli_upload_inputs_parser(input_path: str) -> BulkUploadInputs:
    """
    Mandatory cli callback
    input string value to typed Dict with pydantic type values
    """
    try:
        logger.debug("-----DEBUG cli_inputs_parser inputs str to pydantic object ---")
        logger.debug(input_path)

        paths = [p for p in input_path.split("," | None)]
        dir_inputs_list = [DirectoryInput(path=DirectoryPath(path)) for path in paths]

        return BulkUploadInputs(
            directory_paths=BatchDirectoryInput(directories=List[dir_inputs_list])
        )
    except Exception as e:
        logger.error(e)
        raise typer.Abort()


def validate_upload_inputs(inputs: BulkUploadInputs):
    """
    Optional verify inputs are usable callback
    note: fastapi only validates input is a pydantic object
    this fastapi Depends callback checks if files exists in directory
    """
    try:
        logger.debug("-----validate inputs ---")
        dir_path_list = [
            dir_input.path
            for dir_input in inputs["directory_paths"].directories
            if dir_input.path
        ]
        logger.debug(dir_path_list)
        for dir_path in dir_path_list:
            files = [f for f in dir_path.iterdir() if f.is_file()]
            logger.debug(files)
            if len(files) < 1:
                raise HTTPException(
                    status_code=400,
                    detail=f'no files_in given directory {dir_path} to upload',
                )
        logger.debug("------validate inputs done ---")
        ## this return object is now ready for use in function
        return inputs
    except Exception as e:
        logger.error("validate bad inputs: %s", e)
        raise HTTPException(
            status_code=400, detail=f"Invalid path inputs for upload: {e}"
        )


def cli_upload_params_parser(p: str) -> BulkUploadParameters:
    """
    Mandatory cli callback
    parameters of type : string, float
    """
    try:
        params = string_to_dict(p)
        logger.debug("-----DEBUG FileParameters parser %s ---", params)
        if len(params) == 2 :
            # check if valid names db are passed in
            return BulkUploadParameters(
                dropdown_database_name=StrictStr(params[0]),
                database_name=StrictStr(params[1]),
            )
        else:
            raise HTTPException(
            status_code=400, detail=f'database upload names, expected 2, actual {p}'
            )
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.error("Invalid parameter input : %s", e)
        raise typer.Abort()


@app.command("bulkupload")
def bulkupload(
    inputs: Annotated[
        BulkUploadInputs,
        typer.Argument(parser=cli_upload_inputs_parser, help="input directory path"),
        Body(embed=True),
        Depends(validate_upload_inputs),
    ],
    parameters: Annotated[
        BulkUploadParameters,
        typer.Argument(
            parser=cli_upload_params_parser, help="input params database name and similarity value "
        ),
        Body(embed=True),
    ] = None,
) -> ResponseBody:
    ''' Upload files from a list of input directories'''
    # If dropdown value chosen is Create a new database, then add database path to available databases, otherwise set
    # database path to dropdown value

    if parameters["dropdown_database_name"] != "Create a new database":
        parameters["database_name"] = parameters["dropdown_database_name"]

        new_database_name = parameters["database_name"]

        # Convert database name to absolute path to database in resources directory
        parameters["database_name"] = os.path.join(
            "data", parameters["database_name"] + ".csv"
        )

        # Check CUDNN compatability
        check_cuDNN_version()

        # Get list of directory paths from input
        input_directory_paths = [
            item.path for item in inputs["directory_paths"].directories
        ]

        print("--------")
        print(parameters)
        print(input_directory_paths)
        print("--------")

        # Call the model function
        response = face_match_model.bulk_upload(
            input_directory_paths[0], parameters["database_name"]
        )

        if (
            response.startswith("Successfully uploaded")
            and response.split(" ")[2] != "0"
        ):
            # Some files were uploaded
            if parameters["dropdown_database_name"] == "Create a new database":
                # Add new database to available databases if database name is not already in available databases
                if parameters["database_name"] not in available_databases:
                    available_databases.append(new_database_name)
    return ResponseBody(root=TextResponse(value=response))
