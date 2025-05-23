import json
import os
from pathlib import Path
from typing import List, TypedDict, Tuple, Union
import concurrent.futures
from threading import Lock

from flask_ml.flask_ml_server import MLServer, load_file_as_string
from flask_ml.flask_ml_server.models import (
    BatchDirectoryInput,
    BatchFileInput,
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

from face_detection_recognition.interface import FaceMatchModel
from face_detection_recognition.utils.GPU import check_cuDNN_version
from face_detection_recognition.utils.logger import log_info
from face_detection_recognition.utils.resource_path import get_resource_path

server = MLServer(__name__)

# Add static location for app-info.md file
script_dir = os.path.dirname(os.path.abspath(__file__))
info_file_path = os.path.join(script_dir, "..", "app-info.md")

server.add_app_metadata(
    name="Face Recognition and Matching",
    author="FaceMatch Team",
    version="2.0.0",
    info=load_file_as_string(info_file_path),
)

# Initialize with "Create a new database" value used in frontend to take new file name entered by user
available_databases: List[str] = ["Create a new database"]

# Load all available datasets under resources/data folder
database_directory_path = get_resource_path("data")
csv_files = list({file.stem for file in Path(database_directory_path).glob("*.csv")})

available_databases.extend(csv_files)

# Read default similarity threshold from config file
config_path = os.path.join(script_dir, "config", "model_config.json")
with open(config_path, "r") as config_file:
    config = json.load(config_file)

default_threshold = config["cosine-threshold"]
# Number of concurrent workers for processing face matches
MAX_WORKERS = 5
# Adjust based on ArcFace + yolov8 threshold=0.48
# MAX_WORKERS = 4  652s
# MAX_WORKERS = 5  638s
# MAX_WORKERS = 6  642s
# Create a lock for thread-safe operations
db_lock = Lock()


# Frontend Task Schema defining inputs and paraneters that users can enter
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
                key="database_name",
                label="Database Name",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key=database_name, label=database_name)
                        for database_name in available_databases[1:]
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


# create an instance of the model
face_match_model = FaceMatchModel()


# Inputs and parameters for the findface endpoint
class FindFaceInputs(TypedDict):
    image_paths: BatchFileInput


class FindFaceParameters(TypedDict):
    database_name: str
    similarity_threshold: float


# Function to process a single face match
def process_face_match(
    image_path: str, similarity_threshold: float, database_path: str
) -> Tuple[bool, Union[List[str], str]]:
    # Acquire lock when accessing the shared model (if necessary)
    with db_lock:
        return face_match_model.find_face(
            image_path, similarity_threshold, database_path
        )


# Endpoint that is used to find matches to a query image
@server.route(
    "/findface",
    order=1,
    short_title="Find Matching Faces",
    task_schema_func=get_ingest_query_image_task_schema,
)
def find_face_endpoint(
    inputs: FindFaceInputs, parameters: FindFaceParameters
) -> ResponseBody:

    # Get list of file paths from input
    input_file_paths = [item.path for item in inputs["image_paths"].files]

    # Convert database name to relative path to data directory in resources folder
    database_path = os.path.join("data", parameters["database_name"] + ".csv")

    # Check CUDNN compatibility
    check_cuDNN_version()

    # Process multiple images in parallel using ThreadPoolExecutor
    all_results = []
    all_statuses = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Create a list of futures for each image
        future_to_image = {
            executor.submit(
                process_face_match,
                image_path,
                parameters["similarity_threshold"],
                database_path,
            ): image_path
            for image_path in input_file_paths
        }

        # Process results as they become available
        for future in concurrent.futures.as_completed(future_to_image):
            image_path = future_to_image[future]
            try:
                status, results = future.result()
                all_statuses.append(status)

                # Log results for debugging
                log_info(f"Image {image_path}: {status}")
                log_info(results)

                if status:
                    all_results.extend(results)
                else:
                    # Return error message if any image processing fails
                    return ResponseBody(
                        root=TextResponse(
                            value=f"Error processing {image_path}: {results}"
                        )
                    )

            except Exception as e:
                log_info(f"Image {image_path} generated an exception: {e}")
                return ResponseBody(
                    root=TextResponse(value=f"Error processing {image_path}: {str(e)}")
                )

    # Create response object of images
    if not all_results:
        return ResponseBody(root=TextResponse(value="No matching faces found"))

    image_results = [
        FileResponse(file_type="img", path=res, title=res) for res in all_results
    ]

    return ResponseBody(root=BatchFileResponse(files=image_results))


# Frontend Task Schema defining inputs and paraneters that users can enter
def get_ingest_images_task_schema() -> TaskSchema:
    return TaskSchema(
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


# Inputs and parameters for the bulkupload endpoint
class BulkUploadInputs(TypedDict):
    directory_paths: BatchDirectoryInput


class BulkUploadParameters(TypedDict):
    dropdown_database_name: str
    database_name: str


# Endpoint to allow users to upload images to database
@server.route(
    "/bulkupload",
    order=0,
    short_title="Upload Images to Database",
    task_schema_func=get_ingest_images_task_schema,
)
def bulk_upload_endpoint(
    inputs: BulkUploadInputs, parameters: BulkUploadParameters
) -> ResponseBody:
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
    log_info(input_directory_paths[0])
    # Call the model function
    response = face_match_model.bulk_upload(
        input_directory_paths[0], parameters["database_name"]
    )

    log_info(response)

    if response.startswith("Successfully uploaded") and response.split(" ")[2] != "0":
        # Some files were uploaded
        if parameters["dropdown_database_name"] == "Create a new database":
            # Add new database to available databases if database name is not already in available databases
            if parameters["database_name"] not in available_databases:
                available_databases.append(new_database_name)
    return ResponseBody(root=TextResponse(value=response))


server.run()
