import json
import os
import multiprocessing
from pathlib import Path
from typing import List, TypedDict, Tuple, Union
import concurrent.futures
from functools import partial

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

# Determine optimal number of workers based on CPU count
# Usually optimal number is CPU count - 1 to leave one core for system processes
# Note: This is not as good as using ThreadPoolExecutor, but it is a simple way to determine number of workers
CPU_COUNT = multiprocessing.cpu_count()
MAX_WORKERS = max(1, CPU_COUNT - 1)

# Initialize server
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

# Initialize with "Create a new database" value used in frontend
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

# Cache for model instances to avoid recreation in each process
# Note: Each process will have its own model instance
model_cache = {}


# Function to get or create a FaceMatchModel instance
def get_model():
    # Get current process ID
    pid = os.getpid()

    # Create a new model instance if it doesn't exist for this process
    if pid not in model_cache:
        log_info(f"Creating new model instance for process {pid}")
        model_cache[pid] = FaceMatchModel()

    return model_cache[pid]


# Function to process a single face match that will run in a separate process
def process_face_match(
    image_path: str, similarity_threshold: float, database_path: str
) -> Tuple[bool, Union[List[str], str]]:
    try:
        # Get model instance for this process
        model = get_model()

        # Log which process is handling this image
        process_id = os.getpid()
        log_info(f"Process {process_id} processing image: {image_path}")

        # Run face matching
        status, results = model.find_face(
            image_path, similarity_threshold, database_path
        )

        return status, results
    except Exception as e:
        # Catch any exceptions that might occur during processing
        log_info(f"Error in process {os.getpid()}: {str(e)}")
        return False, f"Processing error: {str(e)}"


# Frontend Task Schema defining inputs and parameters
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


# Create a shared model instance for the main process
face_match_model = FaceMatchModel()


# Inputs and parameters for the findface endpoint
class FindFaceInputs(TypedDict):
    image_paths: BatchFileInput


class FindFaceParameters(TypedDict):
    database_name: str
    similarity_threshold: float


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

    if not input_file_paths:
        return ResponseBody(root=TextResponse(value="No input images provided"))

    # Convert database name to relative path to data directory in resources folder
    database_path = os.path.join("data", parameters["database_name"] + ".csv")

    # Check CUDNN compatibility
    check_cuDNN_version()

    # For small number of images (e.g., 1-2), it might be faster to just process sequentially
    if len(input_file_paths) < 2:
        log_info("Processing single image without multiprocessing")
        status, results = face_match_model.find_face(
            input_file_paths[0], parameters["similarity_threshold"], database_path
        )

        if not status:
            return ResponseBody(root=TextResponse(value=results))

        image_results = [
            FileResponse(file_type="img", path=res, title=res) for res in results
        ]

        return ResponseBody(root=BatchFileResponse(files=image_results))

    # Process multiple images in parallel using ProcessPoolExecutor
    log_info(
        f"Processing {len(input_file_paths)} images with {MAX_WORKERS} worker processes"
    )
    all_results = []

    # Create a partial function with fixed parameters
    process_func = partial(
        process_face_match,
        similarity_threshold=parameters["similarity_threshold"],
        database_path=database_path,
    )

    # Use ProcessPoolExecutor for true parallel processing
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks to the executor
        future_to_image = {
            executor.submit(process_func, image_path): image_path
            for image_path in input_file_paths
        }

        # Process results as they become available
        for future in concurrent.futures.as_completed(future_to_image):
            image_path = future_to_image[future]
            try:
                status, results = future.result()

                # Log results for debugging
                log_info(f"Completed processing image {image_path}: {status}")

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
                log_info(f"Exception for image {image_path}: {e}")
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


# Frontend Task Schema defining inputs and parameters for users
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

    # Check CUDNN compatibility
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


if __name__ == "__main__":
    server.run()
