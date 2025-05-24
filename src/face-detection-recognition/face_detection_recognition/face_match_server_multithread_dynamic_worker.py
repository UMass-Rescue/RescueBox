import json
import os
import time
import psutil
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
# Create a lock for thread-safe operations
db_lock = Lock()


# 709s
class DynamicWorkerPool:
    """
    Dynamically allocates workers based on system resources
    """

    def __init__(self, min_workers=2, max_workers=8):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.current_workers = min_workers
        self.lock = Lock()
        self.last_check_time = 0
        self.check_interval = 1.0  # seconds

    def get_worker_count(self):
        """
        Calculate optimal worker count based on system conditions
        """
        current_time = time.time()
        # Only check system resources periodically to avoid overhead
        if current_time - self.last_check_time < self.check_interval:
            return self.current_workers

        with self.lock:
            self.last_check_time = current_time

            # Check CPU load
            cpu_usage = psutil.cpu_percent(interval=0.1)

            # Check memory availability
            memory_info = psutil.virtual_memory()
            available_memory_gb = memory_info.available / (1024 * 1024 * 1024)  # in GB
            memory_percent = memory_info.percent

            # Check GPU utilization if available
            gpu_utilization = self._check_gpu_utilization()

            # Calculate optimal worker count based on system conditions
            new_worker_count = self.current_workers

            # Adjust based on CPU
            if cpu_usage > 80 and new_worker_count > self.min_workers:
                new_worker_count -= 1
                log_info(f"Reducing workers due to high CPU usage ({cpu_usage}%)")
            elif cpu_usage < 50 and new_worker_count < self.max_workers:
                new_worker_count += 1
                log_info(f"Increasing workers due to low CPU usage ({cpu_usage}%)")

            # Adjust based on memory
            if memory_percent > 85 and new_worker_count > self.min_workers:
                new_worker_count -= 1
                log_info(
                    f"Reducing workers due to high memory usage ({memory_percent}%)"
                )
            elif available_memory_gb < 1.0 and new_worker_count > self.min_workers:
                new_worker_count -= 1
                log_info(
                    f"Reducing workers due to low available memory ({available_memory_gb:.2f} GB)"
                )

            # Adjust based on GPU if available
            if gpu_utilization > 90 and new_worker_count > self.min_workers:
                new_worker_count -= 1
                log_info(
                    f"Reducing workers due to high GPU utilization ({gpu_utilization}%)"
                )

            # Update current workers
            if new_worker_count != self.current_workers:
                log_info(
                    f"Adjusting worker count from {self.current_workers} to {new_worker_count}"
                )
                self.current_workers = new_worker_count

            return self.current_workers

    def _check_gpu_utilization(self):
        """
        Check GPU utilization if available
        Returns utilization percentage or 0 if not available
        """
        try:
            # Try to import pynvml for NVIDIA GPU monitoring
            import pynvml

            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()

            if device_count > 0:
                # Use the first GPU for simplicity
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                pynvml.nvmlShutdown()
                return utilization.gpu  # Return GPU utilization percentage

        except (ImportError, Exception):
            # GPU monitoring not available or failed
            pass

        return 0  # Default if GPU monitoring is not available


# Create worker pool instance
worker_pool = DynamicWorkerPool(min_workers=2, max_workers=8)


class SystemHealthMonitor:
    """
    Monitors system health and implements circuit breaking
    """

    def __init__(self, threshold_cpu=90, threshold_memory=90):
        self.threshold_cpu = threshold_cpu
        self.threshold_memory = threshold_memory
        self.circuit_open = False
        self.last_check = 0
        self.check_interval = 5  # seconds
        self.recovery_time = 30  # seconds
        self.circuit_open_time = 0

    def is_healthy(self):
        """
        Check if the system is healthy enough to process requests
        """
        current_time = time.time()

        # If circuit is open, check if recovery time has passed
        if self.circuit_open:
            if current_time - self.circuit_open_time > self.recovery_time:
                log_info("Circuit breaker recovery time passed, checking system health")
                self.circuit_open = False
            else:
                return False

        # Only check system metrics periodically
        if current_time - self.last_check < self.check_interval:
            return not self.circuit_open

        self.last_check = current_time
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent

        log_info(f"System health check: CPU {cpu_usage}%, Memory {memory_usage}%")

        # Check if system is overloaded
        if cpu_usage > self.threshold_cpu or memory_usage > self.threshold_memory:
            log_info(f"System overloaded: CPU {cpu_usage}%, Memory {memory_usage}%")
            self.circuit_open = True
            self.circuit_open_time = current_time
            return False

        return True


# Create health monitor instance
health_monitor = SystemHealthMonitor(threshold_cpu=90, threshold_memory=90)


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


def estimate_image_complexity(image_path):
    """
    Estimate the computational complexity of processing an image
    Returns a complexity score (higher = more complex)
    """
    try:
        # Get image file size in MB
        file_size = os.path.getsize(image_path) / (1024 * 1024)

        # Could be extended to check image dimensions, color depth, etc.
        # For now, use file size as a simple proxy for complexity

        return file_size
    except Exception as e:
        log_info(f"Error estimating image complexity: {e}")
        return 1.0  # Default medium complexity


# Function to process a single face match
def process_face_match(
    image_path: str, similarity_threshold: float, database_path: str
) -> Tuple[bool, Union[List[str], str]]:
    """
    Process a single face match request
    """
    # Log processing start
    start_time = time.time()
    log_info(f"Processing image: {image_path}")

    # Acquire lock when accessing the shared model (if necessary)
    # If your model is thread-safe, you might not need this lock
    with db_lock:
        result = face_match_model.find_face(
            image_path, similarity_threshold, database_path
        )

    # Log processing time
    processing_time = time.time() - start_time
    log_info(f"Processed {image_path} in {processing_time:.2f} seconds")

    return result


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
    # Check system health before processing
    if not health_monitor.is_healthy():
        return ResponseBody(
            root=TextResponse(
                value="System is currently overloaded. Please try again later."
            )
        )

    # Get list of file paths from input
    input_file_paths = [item.path for item in inputs["image_paths"].files]

    # Log request info
    log_info(f"Received request to find faces in {len(input_file_paths)} images")

    # Convert database name to relative path to data directory in resources folder
    database_path = os.path.join("data", parameters["database_name"] + ".csv")

    # Check CUDNN compatibility
    check_cuDNN_version()

    # Sort images by complexity for better load distribution
    input_files_with_complexity = [
        (path, estimate_image_complexity(path)) for path in input_file_paths
    ]

    # Sort by complexity (process simpler images first)
    input_files_with_complexity.sort(key=lambda x: x[1])
    sorted_input_files = [item[0] for item in input_files_with_complexity]

    log_info(f"Sorted {len(sorted_input_files)} images by complexity")

    # Get dynamic worker count based on current system load
    worker_count = worker_pool.get_worker_count()
    log_info(f"Using {worker_count} workers for processing")

    # Process multiple images in parallel using ThreadPoolExecutor with dynamic worker count
    all_results = []
    all_statuses = []
    error_messages = []

    # Track overall processing time
    overall_start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        # Create a list of futures for each image
        future_to_image = {
            executor.submit(
                process_face_match,
                image_path,
                parameters["similarity_threshold"],
                database_path,
            ): image_path
            for image_path in sorted_input_files
        }

        # Process results as they become available
        for future in concurrent.futures.as_completed(future_to_image):
            image_path = future_to_image[future]
            try:
                status, results = future.result()
                all_statuses.append(status)

                # Log results for debugging
                log_info(f"Image {image_path}: {status}")

                if status:
                    if isinstance(results, list):
                        all_results.extend(results)
                    else:
                        log_info(
                            f"Unexpected result type for {image_path}: {type(results)}"
                        )
                else:
                    error_msg = f"Error processing {image_path}: {results}"
                    log_info(error_msg)
                    error_messages.append(error_msg)

            except Exception as e:
                error_msg = f"Exception processing {image_path}: {str(e)}"
                log_info(error_msg)
                error_messages.append(error_msg)

    # Calculate and log total processing time
    overall_processing_time = time.time() - overall_start_time
    log_info(f"Total processing time: {overall_processing_time:.2f} seconds")

    # Handle error cases
    if error_messages and not all_results:
        # If all images failed, return combined error message
        combined_error = "\n".join(error_messages)
        return ResponseBody(root=TextResponse(value=combined_error))

    # Create response object of images
    if not all_results:
        return ResponseBody(root=TextResponse(value="No matching faces found"))

    # If some images succeeded but others failed, include warnings in response
    image_results = [
        FileResponse(file_type="img", path=res, title=res) for res in all_results
    ]

    # Include any error messages as part of the response metadata if needed
    # Could be extended to include error warnings in the response

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
    # Check system health before processing
    if not health_monitor.is_healthy():
        return ResponseBody(
            root=TextResponse(
                value="System is currently overloaded. Please try again later."
            )
        )

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

    # Log start time
    start_time = time.time()
    log_info(f"Starting bulk upload from directory: {input_directory_paths[0]}")

    # Call the model function
    response = face_match_model.bulk_upload(
        input_directory_paths[0], parameters["database_name"]
    )

    # Log completion time
    upload_time = time.time() - start_time
    log_info(f"Bulk upload completed in {upload_time:.2f} seconds")
    log_info(response)

    if response.startswith("Successfully uploaded") and response.split(" ")[2] != "0":
        # Some files were uploaded
        if parameters["dropdown_database_name"] == "Create a new database":
            # Add new database to available databases if database name is not already in available databases
            if parameters["database_name"] not in available_databases:
                available_databases.append(new_database_name)
    return ResponseBody(root=TextResponse(value=response))


# Start the server
if __name__ == "__main__":
    log_info("Starting Face Recognition and Matching server")
    log_info(f"Available databases: {available_databases}")
    server.run()
