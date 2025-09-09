import json
import os
import typer
from dotenv import load_dotenv
from typing import List, TypedDict

from rb.lib.ml_service import MLService
from rb.api.models import (
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
    IntParameterDescriptor,
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
    version="2.1.0",
    info=info,
    gpu=True,
)

IMAGE_EXTENSIONS = {".jpg", ".png"}


class ImageDirectory(FileFilterDirectory):
    path: DirectoryPath
    file_extensions: List[str] = IMAGE_EXTENSIONS


# Initialize with "Create a new collection" value used in frontend to take new file name entered by user
available_collections: List[str] = ["Create a new collection"]

available_multi_pipeline_collections: List[str] = ["Create a new collection"]

# single pipeline collections
available_collections.extend(DB.get_available_collections(isEnsemble=False))

# mutiple pipeline collections
available_multi_pipeline_collections.extend(
    DB.get_available_collections(isEnsemble=True)
)

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

    full_collection_name = DB.create_full_collection_name(
        parameters["collection_name"],
        config["detector_backend"],
        config["model_name"],
        False,
    )
    # Call model function to find matches
    status, results = face_match_model.find_face(
        input_file_paths[0],
        parameters["similarity_threshold"],
        full_collection_name,
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

    full_collection_name = DB.create_full_collection_name(
        parameters["collection_name"],
        config["detector_backend"],
        config["model_name"],
        False,
    )

    # Call model function to find matches
    status, results = face_match_model.find_face_bulk(
        inputs["query_directory"].path,
        parameters["similarity_threshold"],
        full_collection_name,
    )
    log_info(status)

    file_responses = []
    if status and results:
        for query_img_name, matched_paths in results.items():
            # Ensure matched_paths is a list, even if it's a single path
            if not isinstance(matched_paths, list):
                matched_paths = [matched_paths]

            for matched_path in matched_paths:
                # Extract filename from the matched_path for the title
                matched_filename = os.path.basename(matched_path)
                file_responses.append(
                    FileResponse(
                        file_type="img",
                        path=matched_path,
                        title=f"Match for {query_img_name}: {matched_filename}",
                        metadata={"query_image": query_img_name}
                    )
                )
    
    if not status or not file_responses:
        # If results is a string (e.g., an error message), use it directly
        # Otherwise, convert the dictionary to a string representation
        error_message = str(results) if isinstance(results, str) else json.dumps(results, indent=2)
        return ResponseBody(root=TextResponse(value=error_message))
    
    return ResponseBody(root=BatchFileResponse(files=file_responses))

server.add_ml_service(
    rule="/findfacebulk",
    ml_function=find_face_bulk_endpoint,
    order=1,
    short_title="Face Find Bulk",
    is_workflow_step=True,
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

    full_collection_name = DB.create_full_collection_name(
        parameters["collection_name"],
        config["detector_backend"],
        config["model_name"],
        False,
    )

    # Call model function to find matches
    status, results = face_match_model.find_face_bulk(
        inputs["query_directory"].path,
        None,
        full_collection_name,
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
    if (
        parameters["dropdown_collection_name"] == available_collections[0]
        and parameters["collection_name"] in available_collections
    ):
        collection_name = (
            "new-collection"
            if parameters["collection_name"] == available_collections[0]
            else parameters["collection_name"]
        )
        default_named_collections = list(
            filter(lambda name: collection_name in name, available_collections)
        )
        # map names to indices (i.e. number at the end of default collection name)
        used_indices = list(
            map(
                lambda name: name.split(f"{collection_name}-")[-1],
                default_named_collections,
            )
        )
        # if any index == "collection", replace with index 0
        used_indices = list(
            map(lambda index: 0 if not index.isdigit() else int(index), used_indices)
        )
        # gets the minimum unused index for differentiating unnamed collections
        index = (
            0
            if len(used_indices) == 0
            else min(set(range(0, max(used_indices) + 2)) - set(used_indices))
        )
        index_str = "" if index == 0 else f"-{index}"
        base_collection_name = f"{collection_name}{index_str}"

    elif parameters["dropdown_collection_name"] != available_collections[0]:
        base_collection_name = parameters["dropdown_collection_name"]
    else:
        base_collection_name = parameters["collection_name"]

    # Check CUDNN compatability
    check_cuDNN_version()
    # Get list of directory paths from input
    input_directory_path = str(inputs["directory_path"].path)
    log_info(input_directory_path)
    full_collection_name = DB.create_full_collection_name(
        base_collection_name,
        config["detector_backend"],
        config["model_name"],
        False,
    )
    # Call the model function
    response = face_match_model.bulk_upload(input_directory_path, full_collection_name)

    if response.startswith("Successfully uploaded") and response.split(" ")[2] != "0":
        # Some files were uploaded
        if parameters["dropdown_collection_name"] == available_collections[0]:
            # Add new collection to available collections if collection name is not already in available collections
            if base_collection_name not in available_collections:
                available_collections.append(base_collection_name)
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
    order=0,
    is_workflow_step=True,
    task_schema_func=get_ingest_images_task_schema,
)

""" 
******************************************************************************************************

Multi-Pipeline Bulk Upload (runs through 4 different configurations)

******************************************************************************************************
"""


# Frontend Task Schema defining inputs and parameters that users can enter
def get_multi_pipeline_ingest_images_task_schema() -> TaskSchema:
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
                        for collection_name in available_multi_pipeline_collections
                    ],
                    message_when_empty="No collections found",
                    default=(
                        available_multi_pipeline_collections[0]
                        if len(available_multi_pipeline_collections) > 0
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


def multi_pipeline_bulk_upload_cli_parser(inputs):
    directory_path = inputs
    return {"directory_path": DirectoryInput(path=directory_path)}


def multi_pipeline_bulk_upload_param_parser(params):
    dropdown_collection_name, collection_name = params.split(",")
    return {
        "dropdown_collection_name": dropdown_collection_name,
        "collection_name": collection_name,
    }


class MultiPipelineBulkUploadInputs(TypedDict):
    directory_path: ImageDirectory


class MultiPipelineBulkUploadParameters(TypedDict):
    dropdown_collection_name: str
    collection_name: str


# Helper function to run a pipeline with modified config
def run_pipeline_with_config(
    config_path, original_config, pipeline_config, operation_func
):
    try:
        # Update config with pipeline settings
        modified_config = original_config.copy()
        modified_config["detector_backend"] = pipeline_config["detector"]
        modified_config["model_name"] = pipeline_config["model"]

        # Write modified config to file
        with open(config_path, "w") as f:
            json.dump(modified_config, f, indent=2)

        # Run the operation function
        result = operation_func()

        # Restore original config
        with open(config_path, "w") as f:
            json.dump(original_config, f, indent=2)

        return True, result

    except Exception as e:
        # Ensure original config is restored
        try:
            with open(config_path, "w") as f:
                json.dump(original_config, f, indent=2)
        except Exception:
            pass

        return False, str(e)


# Endpoint to upload images with 4 different pipeline configurations
def multi_pipeline_bulk_upload_endpoint(
    inputs: MultiPipelineBulkUploadInputs, parameters: MultiPipelineBulkUploadParameters
) -> ResponseBody:
    check_cuDNN_version()
    if (
        parameters["dropdown_collection_name"]
        == available_multi_pipeline_collections[0]
        and parameters["collection_name"] in available_multi_pipeline_collections
    ):
        collection_name = (
            "new-collection"
            if parameters["collection_name"] == available_multi_pipeline_collections[0]
            else parameters["collection_name"]
        )
        default_named_collections = list(
            filter(
                lambda name: collection_name in name,
                available_multi_pipeline_collections,
            )
        )
        # map names to indices (i.e. number at the end of default collection name)
        used_indices = list(
            map(
                lambda name: name.split(f"{collection_name}-")[-1],
                default_named_collections,
            )
        )
        # if any index == "collection", replace with index 0
        used_indices = list(
            map(lambda index: 0 if not index.isdigit() else int(index), used_indices)
        )
        # gets the minimum unused index for differentiating unnamed collections
        index = (
            0
            if len(used_indices) == 0
            else min(set(range(0, max(used_indices) + 2)) - set(used_indices))
        )
        index_str = "" if index == 0 else f"-{index}"
        base_collection_name = f"{collection_name}{index_str}"

    elif (
        parameters["dropdown_collection_name"]
        != available_multi_pipeline_collections[0]
    ):
        base_collection_name = parameters["dropdown_collection_name"]
    else:
        base_collection_name = parameters["collection_name"]

    base_path = str(inputs["directory_path"].path)

    pipeline_configs = [
        {"detector": "retinaface", "model": "Facenet512"},  # default configuration
        {"detector": "retinaface", "model": "ArcFace"},
        {"detector": "yolov8", "model": "Facenet512"},
        {"detector": "yolov8", "model": "ArcFace"},
    ]

    # Import the resource_path utility from the same location as face_match_model
    from face_detection_recognition.utils.resource_path import get_config_path

    config_path = get_config_path("model_config.json")

    # Read the original config
    try:
        with open(config_path, "r") as f:
            original_config = json.load(f)
    except Exception as e:
        return ResponseBody(
            root=TextResponse(value=f"Error reading config file: {str(e)}")
        )

    results = []
    for config in pipeline_configs:
        # Generate collection name for this pipeline
        full_collection_name = DB.create_full_collection_name(
            base_collection_name,
            config["detector"],
            config["model"],
            True,
        )

        def operation():
            return face_match_model.bulk_upload(base_path, full_collection_name)

        success, result = run_pipeline_with_config(
            config_path, original_config, config, operation
        )

        pipeline_name = f"{config['detector']}/{config['model']}"
        if success:
            results.append(f"{pipeline_name}: {result}")
            # Add to available collections if not already there
            if base_collection_name not in available_multi_pipeline_collections:
                available_multi_pipeline_collections.append(base_collection_name)
        else:
            results.append(f"{pipeline_name}: Error: {result}")

    combined_result = "Results by pipeline:\n" + "\n".join(results)
    return ResponseBody(root=TextResponse(value=combined_result))


# server.add_ml_service(
#     rule="/multi_pipeline_bulkupload",
#     ml_function=multi_pipeline_bulk_upload_endpoint,
#     inputs_cli_parser=typer.Argument(
#         parser=multi_pipeline_bulk_upload_cli_parser, help="Directory to images to upload"
#     ),
#     parameters_cli_parser=typer.Argument(
#         parser=multi_pipeline_bulk_upload_param_parser, help="Collection name base"
#     ),
#     short_title="Multi-Pipeline Bulk Upload",
#     order=6,
#     task_schema_func=get_multi_pipeline_ingest_images_task_schema,
# )

""" 
******************************************************************************************************

Multi-Pipeline Face Find Bulk (runs bulk query through 4 different configurations with weighted voting)

******************************************************************************************************
"""


# Frontend Task Schema defining inputs and parameters that users can enter
def get_multi_pipeline_face_find_bulk_task_schema() -> TaskSchema:
    return TaskSchema(
        inputs=[
            InputSchema(
                key="directory_path",
                label="Query Directory",
                input_type=InputType.DIRECTORY,
            )
        ],
        parameters=[
            ParameterSchema(
                key="collection_name",
                label="Choose Collection",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=collection_name, label=collection_name)
                        for collection_name in available_multi_pipeline_collections[1:]
                    ],
                    message_when_empty="No collections found",
                    default=(
                        available_multi_pipeline_collections[0]
                        if len(available_multi_pipeline_collections) > 0
                        else ""
                    ),
                ),
            ),
            ParameterSchema(
                key="threshold_mode",
                label="Threshold Mode",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        {"key": "strict", "label": "Strict (Higher Thresholds)"},
                        {"key": "relaxed", "label": "Relaxed (Lower Thresholds)"},
                    ],
                    default="strict",
                ),
            ),
            ParameterSchema(
                key="min_votes",
                label="Minimum Votes Required",
                value=IntParameterDescriptor(default=3, min=1, max=5),
            ),
        ],
    )


def multi_pipeline_face_find_bulk_cli_parser(inputs):
    directory_path = inputs
    return {"directory_path": DirectoryInput(path=directory_path)}


def multi_pipeline_face_find_bulk_param_parser(params):
    parts = params.split(",")
    if len(parts) == 3:
        collection_name, threshold_mode, min_votes = parts
        return {
            "collection_name": collection_name,
            "threshold_mode": threshold_mode,
            "min_votes": int(min_votes),
        }
    else:
        collection_name, threshold_mode = parts
        return {
            "collection_name": collection_name,
            "threshold_mode": threshold_mode,
            "min_votes": 3,  # Default to 3 (majority)
        }


class MultiPipelineFindFaceBulkInputs(TypedDict):
    directory_path: ImageDirectory


class MultiPipelineFindFaceBulkParameters(TypedDict):
    collection_name: str
    threshold_mode: str
    min_votes: int


# Endpoint that runs bulk face finding with 4 different pipeline configurations and weighted voting
def multi_pipeline_face_find_bulk_endpoint(
    inputs: MultiPipelineFindFaceBulkInputs,
    parameters: MultiPipelineFindFaceBulkParameters,
) -> ResponseBody:
    query_directory = str(inputs["directory_path"].path)
    threshold_mode = parameters.get("threshold_mode", "strict")
    min_votes = parameters.get("min_votes", 3)  # Default to 3 if not provided

    check_cuDNN_version()

    # Define threshold sets
    strict_thresholds = {
        "retinaface_Facenet512": 0.66,
        "retinaface_ArcFace": 0.50,
        "yolov8_Facenet512": 0.64,
        "yolov8_ArcFace": 0.48,
    }

    relaxed_thresholds = {
        "retinaface_Facenet512": 0.56,
        "retinaface_ArcFace": 0.44,
        "yolov8_Facenet512": 0.56,
        "yolov8_ArcFace": 0.44,
    }

    thresholds = strict_thresholds if threshold_mode == "strict" else relaxed_thresholds

    # Define the four different pipeline configurations with their voting weights
    pipeline_configs = [
        {
            "detector": "retinaface",
            "model": "Facenet512",
            "weight": 2,
            "threshold": thresholds["retinaface_Facenet512"],
        },
        {
            "detector": "retinaface",
            "model": "ArcFace",
            "weight": 1,
            "threshold": thresholds["retinaface_ArcFace"],
        },
        {
            "detector": "yolov8",
            "model": "Facenet512",
            "weight": 1,
            "threshold": thresholds["yolov8_Facenet512"],
        },
        {
            "detector": "yolov8",
            "model": "ArcFace",
            "weight": 1,
            "threshold": thresholds["yolov8_ArcFace"],
        },
    ]

    # Import the resource_path utility from the same location as face_match_model
    from face_detection_recognition.utils.resource_path import get_config_path

    config_path = get_config_path("model_config.json")

    # Read the original config
    try:
        with open(config_path, "r") as f:
            original_config = json.load(f)
    except Exception as e:
        return ResponseBody(
            root=TextResponse(value=f"Error reading config file: {str(e)}")
        )

    # Helper function to run a pipeline with modified config
    def run_pipeline_with_config(
        config_path, original_config, pipeline_config, operation_func
    ):
        try:
            # Update config with pipeline settings
            modified_config = original_config.copy()
            modified_config["detector_backend"] = pipeline_config["detector"]
            modified_config["model_name"] = pipeline_config["model"]

            # Write modified config to file
            with open(config_path, "w") as f:
                json.dump(modified_config, f, indent=2)

            result = operation_func()

            # Restore original config
            with open(config_path, "w") as f:
                json.dump(original_config, f, indent=2)

            return True, result

        except Exception as e:
            # Ensure original config is restored
            try:
                with open(config_path, "w") as f:
                    json.dump(original_config, f, indent=2)
            except Exception:
                pass

            return False, str(e)

    all_pipeline_results = {}
    vote_tracking = {}  # To track votes for each match
    match_details = {}  # To track which pipelines found each match
    img_files = []

    try:
        img_files = [
            f
            for f in os.listdir(query_directory)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp"))
        ]
        img_files.sort()
    except Exception as e:
        return ResponseBody(
            root=TextResponse(value=f"Error listing query directory: {str(e)}")
        )

    for img in img_files:
        vote_tracking[img] = {}
        match_details[img] = {}

    # Process each pipeline and collect votes
    for config in pipeline_configs:
        full_collection_name = DB.create_full_collection_name(
            parameters["collection_name"],
            config["detector"],
            config["model"],
            True,
        )

        current_threshold = config["threshold"]

        def operation():
            status, results = face_match_model.find_face_bulk(
                query_directory,
                current_threshold,
                full_collection_name,
                similarity_filter=True,
            )
            return status, results

        pipeline_name = f"{config['detector']}/{config['model']}"
        success, result = run_pipeline_with_config(
            config_path, original_config, config, operation
        )

        if success:
            status, results = result
            all_pipeline_results[pipeline_name] = {
                "status": status,
                "results": results,
                "threshold": current_threshold,
            }

            if status and results:
                # Process votes from this pipeline
                for query_img, matches in results.items():
                    if query_img not in vote_tracking:
                        vote_tracking[query_img] = {}
                        match_details[query_img] = {}

                    for match in matches:
                        # Initialize if this is the first time seeing this match
                        if match not in vote_tracking[query_img]:
                            vote_tracking[query_img][match] = 0
                            match_details[query_img][match] = []

                        # Add votes based on pipeline weight
                        vote_tracking[query_img][match] += config["weight"]
                        match_details[query_img][match].append(pipeline_name)
        else:
            all_pipeline_results[pipeline_name] = {
                "status": False,
                "results": result,
                "threshold": current_threshold,
            }

    # Process votes to determine final matches
    final_results = {}
    for query_img in vote_tracking:
        final_results[query_img] = []
        for match, votes in vote_tracking[query_img].items():
            if votes >= min_votes:
                final_results[query_img].append(match)

    text_summary = ""

    # Create a text summary of the results by pipeline
    text_summary += f"Threshold Mode: {threshold_mode.upper()}\n"

    text_summary += "\nResults by pipeline:\n"
    for pipeline, result in all_pipeline_results.items():
        text_summary += f"\n{pipeline} (threshold: {result['threshold']:.2f}): "
        if result["status"]:
            total_matches = sum(
                len(matches) for matches in result["results"].values() if matches
            )
            total_images_with_matches = sum(
                1 for matches in result["results"].values() if matches
            )
            text_summary += f"Found {total_matches} matches across {total_images_with_matches} images"
        else:
            text_summary += f"Error: {result['results']}"

    text_summary += "\n\nWeighted Voting Results:\n"
    text_summary += f"Minimum votes required: {min_votes}\n"
    text_summary += "Pipeline weights: retinaface/Facenet512 (2 votes), all others (1 vote each)\n\n"

    total_images = len(img_files)
    images_with_matches = sum(1 for matches in final_results.values() if matches)
    total_matches = sum(len(matches) for matches in final_results.values())

    text_summary += f"Processed {total_images} images\n"
    text_summary += f"Found matches for {images_with_matches} images\n"
    text_summary += (
        f"Total {total_matches} matches found with at least {min_votes} votes\n\n"
    )

    # Add detailed results per query image
    text_summary += "Results by query image:\n"
    for query_img in sorted(final_results.keys()):
        matches = final_results[query_img]
        if matches:
            text_summary += f"\n{query_img}: {len(matches)} matches found"

            # Add voting details for each match
            for match in matches:
                pipelines = match_details[query_img][match]
                votes = vote_tracking[query_img][match]
                text_summary += (
                    f"\n  - {match} ({votes} votes from {', '.join(pipelines)})"
                )
        else:
            text_summary += (
                f"\n{query_img}: No matches found with at least {min_votes} votes"
            )

    # Create a visual representation of the results
    if final_results:
        # Prepare a list of all matched images for the response
        all_match_paths = []
        for matches in final_results.values():
            for match in matches:
                if match not in all_match_paths:
                    all_match_paths.append(match)

        # Create the response with both summary and image results
        if all_match_paths:
            # Create image response items
            image_results = [
                FileResponse(file_type="img", path=res, title=os.path.basename(res))
                for res in all_match_paths
            ]

            # Create a temporary text file with the summary
            import tempfile

            summary_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".txt", mode="w"
            )
            summary_file.write(text_summary)
            summary_file_path = summary_file.name
            summary_file.close()

            # Add the summary text file as the last item in the response
            image_results.append(
                FileResponse(
                    file_type="text",
                    path=summary_file_path,
                    title="Results_Summary.txt",
                )
            )

            return ResponseBody(
                root=BatchFileResponse(
                    files=image_results,
                    metadata={
                        "summary": "See Results_Summary.txt for detailed results"
                    },
                )
            )

    # If no matches found or error occurred, just return the text summary
    return ResponseBody(root=TextResponse(value=text_summary))


# server.add_ml_service(
#     rule="/multi_pipeline_findfacebulk",
#     ml_function=multi_pipeline_face_find_bulk_endpoint,
#     inputs_cli_parser=typer.Argument(
#         parser=multi_pipeline_face_find_bulk_cli_parser, help="Path to query directory"
#     ),
#     parameters_cli_parser=typer.Argument(
#         parser=multi_pipeline_face_find_bulk_param_parser, help="Collection name base, similarity threshold, and minimum votes"
#     ),
#     short_title="Multi-Pipeline Find Face Bulk",
#     order=7,
#     task_schema_func=get_multi_pipeline_face_find_bulk_task_schema,
# )

""" 
******************************************************************************************************

Delete Collection

******************************************************************************************************
"""


# Frontend Task Schema defining inputs and parameters that users can enter
def delete_collection_task_schema() -> TaskSchema:
    return TaskSchema(
        inputs=[],
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


def delete_collection_cli_parser(input):
    return {}


def delete_collection_parameter_parser(parameter):
    collection_name = parameter
    return {
        "collection_name": collection_name,
    }


# Inputs and parameters for the bulkupload endpoint
class DeleteCollectionInputs(TypedDict):
    pass


class DeleteCollectionParameters(TypedDict):
    collection_name: str


# Endpoint for deleting collections from ChromaDB
def delete_collection_endpoint(
    inputs: DeleteCollectionInputs, parameters: DeleteCollectionParameters
) -> ResponseBody:
    responseValue = ""
    collection_name = parameters["collection_name"]
    full_collection_name = DB.create_full_collection_name(
        parameters["collection_name"],
        config["detector_backend"],
        config["model_name"],
        False,
    )
    try:
        DB.client.delete_collection(full_collection_name)
        responseValue = f"Successfully deleted {full_collection_name}"
        available_collections.remove(collection_name)
        log_info(responseValue)
    except Exception:
        responseValue = f"Collection {full_collection_name} does not exist."
        log_info(responseValue)

    return ResponseBody(root=TextResponse(value=responseValue))


server.add_ml_service(
    rule="/deletecollection",
    ml_function=delete_collection_endpoint,
    inputs_cli_parser=typer.Argument(
        parser=delete_collection_cli_parser, help="Collection name"
    ),
    parameters_cli_parser=typer.Argument(
        parser=delete_collection_parameter_parser, help="Full Collection name"
    ),
    short_title="Delete Collection",
    order=2,
    is_workflow_step=False,
    task_schema_func=delete_collection_task_schema,
)

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

    collection_names = [str(collection) for collection in responseValue]
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
