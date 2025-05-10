import json
import os
import typer
from dotenv import load_dotenv
from typing import List, TypedDict

from rb.lib.ml_service import MLService
from rb.api.models import (
    TextInput,
    BatchTextResponse,
    FileFilterDirectory,
    BatchFileInput,
    DirectoryInput,
    BatchFileResponse,
    EnumParameterDescriptor,
    EnumVal,
    FileResponse,
    FloatRangeDescriptor,
    InputSchema,
    InputType,
    ParameterSchema,
    RangedFloatParameterDescriptor,
    ResponseBody,
    TaskSchema,
    TextParameterDescriptor,
    TextResponse,
)

from pydantic import DirectoryPath

from face_detection_recognition.interface import FaceMatchModel
from face_detection_recognition.utils.GPU import check_cuDNN_version
from face_detection_recognition.utils.logger import log_info
from face_detection_recognition.database_functions import Vector_Database

load_dotenv()

DB = Vector_Database()

APP_NAME = "face-match"
server = MLService(APP_NAME)

# Add static location for app-info.md file
script_dir = os.path.dirname(os.path.abspath(__file__))
info_file_path = os.path.join(script_dir, "app-info.md")

with open(info_file_path, "r") as f:
    info = f.read()

server.add_app_metadata(
    name="Face Recognition and Matching",
    plugin_name=APP_NAME,
    author="FaceMatch Team",
    version="0.1.0",
    info=info,
)

IMAGE_EXTENSIONS = {".jpg", ".png"}


class ImageDirectory(FileFilterDirectory):
    path: DirectoryPath
    file_extensions: List[str] = IMAGE_EXTENSIONS


# Initialize with "Create a new collection" value used in frontend to take new file name entered by user
available_collections: List[str] = ["Create a new collection"]

# Load all available collections from chromaDB
existing_collections = [
    collection.name.split("_")[0] for collection in DB.client.list_collections()
]
available_collections.extend(existing_collections)

# Read default similarity threshold from config file
config_path = os.path.join(script_dir, "config", "model_config.json")
with open(config_path, "r") as config_file:
    config = json.load(config_file)

default_threshold = config["cosine-threshold"]

""" 
******************************************************************************************************

Face Find (single image)

******************************************************************************************************
"""


# Frontend Task Schema defining inputs and parameters that users can enter
def get_ingest_query_image_task_schema() -> TaskSchema:
    return TaskSchema(
        inputs=[
            InputSchema(
                key="image_paths",
                label="Image Path",
                input_type=InputType.BATCHFILE,
            )
        ],
        parameters=[
            ParameterSchema(
                key="collection_name",
                label="Collection Name",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=collection_name, label=collection_name)
                        for collection_name in available_collections[1:]
                    ],
                    message_when_empty="No collections found",
                    default=(available_collections[0]),
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


# create an instance of the model
face_match_model = FaceMatchModel()


def face_find_cli_parser(inputs):
    image_paths = inputs.split(",")
    return {
        "image_paths": BatchFileInput(
            files=[{"path": file_path} for file_path in image_paths]
        )
    }


def face_find_param_parser(params):
    collection_name, similarity_threshold = params.split(",")
    return {
        "collection_name": collection_name,
        "similarity_threshold": float(similarity_threshold),
    }


# Inputs and parameters for the findface endpoint
class FindFaceInputs(TypedDict):
    image_paths: BatchFileInput


class FindFaceParameters(TypedDict):
    collection_name: str
    similarity_threshold: float


# Endpoint that is used to find matches to a query image
def find_face_endpoint(
    inputs: FindFaceInputs, parameters: FindFaceParameters
) -> ResponseBody:

    # Get list of file paths from input
    input_file_paths = [str(item.path) for item in inputs["image_paths"].files]
    # Check CUDNN compatability
    check_cuDNN_version()
    # Call model function to find matches
    status, results = face_match_model.find_face(
        input_file_paths[0],
        parameters["similarity_threshold"],
        parameters["collection_name"],
    )
    log_info(status)
    log_info(results)

    # Create response object of images if status is True
    if not status:
        return ResponseBody(root=TextResponse(value=results))

    image_results = [
        FileResponse(file_type="img", path=res, title=res) for res in results
    ]

    return ResponseBody(root=BatchFileResponse(files=image_results))


# server.add_ml_service(
#     rule="/findface",
#     ml_function=find_face_endpoint,
#     inputs_cli_parser=typer.Argument(
#         parser=face_find_cli_parser, help="Path to query image"
#     ),
#     parameters_cli_parser=typer.Argument(
#         parser=face_find_param_parser, help="Collection name and similarity threshold"
#     ),
#     short_title="Find Face",
#     order=0,
#     task_schema_func=get_ingest_query_image_task_schema,
# )

""" 
******************************************************************************************************

Bulk Face Find (multiple images)

******************************************************************************************************
"""


# Frontend Task Schema defining inputs and parameters that users can enter
def get_ingest_bulk_query_image_task_schema() -> TaskSchema:
    return TaskSchema(
        inputs=[
            InputSchema(
                key="query_directory",
                label="Query Directory",
                input_type=InputType.DIRECTORY,
            )
        ],
        parameters=[
            ParameterSchema(
                key="collection_name",
                label="Collection Name",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=collection_name, label=collection_name)
                        for collection_name in available_collections[1:]
                    ],
                    message_when_empty="No collections found",
                    default=(available_collections[0]),
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


def find_face_bulk_cli_parser(inputs):
    query_directory = inputs
    return {"query_directory": DirectoryInput(path=query_directory)}


def find_face_bulk_param_parser(inputs):
    collection_name, similarity_threshold = inputs.split(",")
    return {
        "collection_name": collection_name,
        "similarity_threshold": float(similarity_threshold),
    }


# Inputs and parameters for the findfacebulk endpoint
class FindFaceBulkInputs(TypedDict):
    query_directory: ImageDirectory


class FindFaceBulkParameters(TypedDict):
    collection_name: str
    similarity_threshold: float


# Endpoint that is used to find matches to a set of query images
def find_face_bulk_endpoint(
    inputs: FindFaceBulkInputs, parameters: FindFaceBulkParameters
) -> ResponseBody:

    # Check CUDNN compatability
    check_cuDNN_version()

    # Call model function to find matches
    status, results = face_match_model.find_face_bulk(
        inputs["query_directory"].path,
        parameters["similarity_threshold"],
        parameters["collection_name"],
    )
    log_info(status)

    return ResponseBody(root=TextResponse(value=str(results)))


server.add_ml_service(
    rule="/findfacebulk",
    ml_function=find_face_bulk_endpoint,
    order=1,
    short_title="Face Find Bulk",
    inputs_cli_parser=typer.Argument(
        parser=find_face_bulk_cli_parser, help="Directory of query images"
    ),
    parameters_cli_parser=typer.Argument(
        parser=find_face_bulk_param_parser,
        help="Collection name, and similarity threshold",
    ),
    task_schema_func=get_ingest_bulk_query_image_task_schema,
)

""" 
******************************************************************************************************

Bulk Face Find Test (no similarity theshold filtering. Results include similarity scores)

******************************************************************************************************
"""


def get_ingest_bulk_test_query_image_task_schema() -> TaskSchema:
    return TaskSchema(
        inputs=[
            InputSchema(
                key="query_directory",
                label="Query Directory",
                input_type=InputType.DIRECTORY,
            )
        ],
        parameters=[
            ParameterSchema(
                key="collection_name",
                label="Collection Name",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=collection_name, label=collection_name)
                        for collection_name in available_collections[1:]
                    ],
                    message_when_empty="No collections found",
                    default=(available_collections[0]),
                ),
            ),
        ],
    )


def find_face_bulk_test_cli_parser(inputs):
    query_directory = inputs
    return {"query_directory": DirectoryInput(path=query_directory)}


def find_face_bulk_test_param_parser(inputs):
    collection_name = inputs
    return {"collection_name": collection_name}


# Inputs and parameters for the findfacebulk endpoint
class FindFaceBulkTestingInputs(TypedDict):
    query_directory: ImageDirectory


class FindFaceBulkTestingParameters(TypedDict):
    collection_name: str


# Endpoint that is used to find matches to a set of query images
# Does not filter by the similarity theshold and returns all results with similarity scores, file paths and
# face index within given query (if multiple faces found in the query, are the results for face 0, 1, etc.)
def find_face_bulk_testing_endpoint(
    inputs: FindFaceBulkTestingInputs, parameters: FindFaceBulkTestingParameters
) -> ResponseBody:

    # Check CUDNN compatability
    check_cuDNN_version()

    # Call model function to find matches
    status, results = face_match_model.find_face_bulk(
        inputs["query_directory"].path,
        None,
        parameters["collection_name"],
        similarity_filter=False,
    )
    log_info(status)

    return ResponseBody(root=TextResponse(value=str(results)))


# server.add_ml_service(
#     rule="/findfacebulktesting",
#     ml_function=find_face_bulk_testing_endpoint,
#     order=2,
#     short_title="Face Find Bulk Test",
#     inputs_cli_parser=typer.Argument(
#         parser=find_face_bulk_test_cli_parser, help="Directory of query images"
#     ),
#     parameters_cli_parser=typer.Argument(
#         parser=find_face_bulk_test_param_parser, help="Collection name"
#     ),
#     task_schema_func=get_ingest_bulk_test_query_image_task_schema,
# )

""" 
******************************************************************************************************

Bulk Upload

******************************************************************************************************
"""


# Frontend Task Schema defining inputs and parameters that users can enter
def get_ingest_images_task_schema() -> TaskSchema:
    return TaskSchema(
        inputs=[
            InputSchema(
                key="directory_path",
                label="Image Directory",
                input_type=InputType.DIRECTORY,
            )
        ],
        parameters=[
            ParameterSchema(
                key="dropdown_collection_name",
                label="Choose Collection",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=collection_name, label=collection_name)
                        for collection_name in available_collections
                    ],
                    message_when_empty="No collections found",
                    default=(
                        available_collections[0]
                        if len(available_collections) > 0
                        else ""
                    ),
                ),
            ),
            ParameterSchema(
                key="collection_name",
                label="New Collection Name (Optional)",
                value=TextParameterDescriptor(default="new-collection"),
            ),
        ],
    )


def bulk_upload_cli_parser(inputs):
    directory_path = inputs
    return {"directory_path": DirectoryInput(path=directory_path)}


def bulk_upload_param_parser(params):
    dropdown_collection_name, collection_name = params.split(",")
    return {
        "dropdown_collection_name": dropdown_collection_name,
        "collection_name": collection_name,
    }


# Inputs and parameters for the bulkupload endpoint
class BulkUploadInputs(TypedDict):
    directory_path: ImageDirectory


class BulkUploadParameters(TypedDict):
    dropdown_collection_name: str
    collection_name: str


# Endpoint to allow users to upload images to chromaDB
def bulk_upload_endpoint(
    inputs: BulkUploadInputs, parameters: BulkUploadParameters
) -> ResponseBody:
    # If dropdown value chosen is Create a new collection, then add collection to available collections, otherwise set
    # collection to dropdown value
    if parameters["collection_name"] in [available_collections[0], "new-collection"]:
        default_named_collections = list(
            filter(lambda name: "new-collection" in name, available_collections)
        )
        # map names to indices (i.e. number at the end of default collection name)
        log_info(default_named_collections)
        used_indices = list(
            map(lambda name: name.split("-")[-1], default_named_collections)
        )
        # if any index == "collection", replace with index 0
        log_info(used_indices)
        used_indices = list(
            map(lambda index: 0 if index == "collection" else int(index), used_indices)
        )
        # gets the minimum unused index for differentiating unnamed collections
        log_info(used_indices)
        index = (
            0
            if len(used_indices) == 0
            else min(
                set(range(min(used_indices), max(used_indices) + 2)) - set(used_indices)
            )
        )
        log_info(index)
        new_collection_name = f"new-collection{"" if index == 0 else f'-{index}'}"

    elif parameters["dropdown_collection_name"] != available_collections[0]:
        new_collection_name = parameters["dropdown_collection_name"]
    else:
        new_collection_name = parameters["collection_name"]
    # log_info("ERROR FOLLOWING THIS LINE **************************")
    # log_info(new_collection_name)
    # Check CUDNN compatability
    check_cuDNN_version()
    # Get list of directory paths from input
    input_directory_path = str(inputs["directory_path"].path)
    log_info(input_directory_path)
    # Call the model function
    response = face_match_model.bulk_upload(input_directory_path, new_collection_name)

    if response.startswith("Successfully uploaded") and response.split(" ")[2] != "0":
        # Some files were uploaded
        if parameters["dropdown_collection_name"] == available_collections[0]:
            # Add new collection to available collections if collection name is not already in available collections
            if new_collection_name not in available_collections:
                available_collections.append(new_collection_name)
    return ResponseBody(root=TextResponse(value=response))


server.add_ml_service(
    rule="/bulkupload",
    ml_function=bulk_upload_endpoint,
    inputs_cli_parser=typer.Argument(
        parser=bulk_upload_cli_parser, help="Directory to images to upload"
    ),
    parameters_cli_parser=typer.Argument(
        parser=bulk_upload_param_parser, help="Collection name"
    ),
    short_title="Bulk Upload",
    order=3,
    task_schema_func=get_ingest_images_task_schema,
)

""" 
******************************************************************************************************

Delete Collection

******************************************************************************************************
"""


# Frontend Task Schema defining inputs and parameters that users can enter
def delete_collection_task_schema() -> TaskSchema:
    return TaskSchema(
        inputs=[
            InputSchema(
                key="collection_name",
                label="Name of collection to delete",
                input_type=InputType.TEXT,
            ),
            InputSchema(
                key="detector_backend",
                label="Detector model of collection",
                input_type=InputType.TEXT,
            ),
            InputSchema(
                key="model_name",
                label="Embedding model of collection",
                input_type=InputType.TEXT,
            ),
        ],
        parameters=[],
    )


def delete_collection_cli_parser(parameters):
    collection_name, detector_backend, model_name = parameters.lower().split(",")
    return {
        "collection_name": collection_name,
        "model_name": model_name,
        "detector_backend": detector_backend,
    }


# Inputs and parameters for the bulkupload endpoint
class DeleteCollectionInputs(TypedDict):
    collection_name: TextInput
    detector_backend: TextInput
    model_name: TextInput


# Endpoint for deleting collections from ChromaDB
def delete_collection_endpoint(
    inputs: DeleteCollectionInputs,
) -> ResponseBody:  # parameters: DeleteCollectionParameters
    responseValue = ""
    collection_name = inputs["collection_name"]
    model_name = inputs["model_name"]
    detector_backend = inputs["detector_backend"]
    try:
        DB.client.delete_collection(
            f"{collection_name}_{detector_backend}_{model_name}"
        )
        responseValue = (
            f"Successfully deleted {collection_name}_{detector_backend}_{model_name}"
        )
        log_info(responseValue)
    except Exception:
        responseValue = f"Collection {collection_name}_{detector_backend}_{model_name} does not exist."
        log_info(responseValue)

    return ResponseBody(root=TextResponse(value=responseValue))


# server.add_ml_service(
#     rule="/deletecollection",
#     ml_function=delete_collection_endpoint,
#     inputs_cli_parser=typer.Argument(
#         parser=delete_collection_cli_parser, help="Collection name"
#     ),
#     short_title="Delete Collection",
#     order=4,
#     task_schema_func=delete_collection_task_schema,
# )

""" 
******************************************************************************************************

List Collections

******************************************************************************************************
"""


def list_collections_task_schema() -> TaskSchema:
    return TaskSchema(inputs=[], parameters=[])


def list_collections_cli_parser(dummy_input):
    return dummy_input


# Inputs and parameters for the bulkupload endpoint
class ListCollectionsInputs(TypedDict):
    pass


# Endpoint for listing all ChromaDB collections
def list_collections_endpoint(inputs: ListCollectionsInputs) -> ResponseBody:

    responseValue = None

    try:
        responseValue = DB.client.list_collections()
        log_info(responseValue)
    except Exception:
        responseValue = ["Failed to List Collections"]
        log_info(responseValue)

    collection_names = [collection.name for collection in responseValue]
    return ResponseBody(
        root=BatchTextResponse(
            texts=[TextResponse(value=collection) for collection in collection_names]
        )
    )


# server.add_ml_service(
#     rule="/listcollections",
#     ml_function=list_collections_endpoint,
#     inputs_cli_parser=typer.Argument(parser=list_collections_cli_parser, help="Empty"),
#     short_title="List Collection",
#     order=5,
#     task_schema_func=list_collections_task_schema,
# )

app = server.app
if __name__ == "__main__":
    app()
