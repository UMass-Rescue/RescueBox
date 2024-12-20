import argparse
import os
from typing import TypedDict
from flask_ml.flask_ml_server import MLServer, load_file_as_string
from flask_ml.flask_ml_server.models import (
    BatchFileInput,
    BatchFileResponse,
    FileResponse, ResponseType, FileType,
    InputSchema,
    InputType,
    ResponseBody,
    TaskSchema,
    DirectoryInput,
    EnumParameterDescriptor,
    EnumVal,
    InputSchema,
    InputType,
    ParameterSchema,
    ResponseBody,
    TaskSchema,
    BatchFileResponse,
    FileResponse,
    FileType,
)
from video_evaluator import VideoEvaluator  
import pdb
import json

# Initialize Flask-ML server
server = MLServer(__name__)

server.add_app_metadata(
    name="XceptionNet Video DeepFake Detector",
    author="UMass Rescue",
    version="0.1.0",
    info=load_file_as_string("app_info.md"),
)

def create_deepfake_detection_task_schema() -> TaskSchema:
    return TaskSchema(
        inputs=[
            InputSchema(
                key="video_paths",
                label="Video Paths",
                input_type=InputType.BATCHFILE,
            ),
            InputSchema(
                key="output_directory",
                label="Output Directory",
                input_type=InputType.DIRECTORY,
            ),
        ],
        parameters=[
            ParameterSchema(
                key="output_format",
                label="Output Format",
                value=EnumParameterDescriptor(
                    enum_vals=[
                        EnumVal(key="json", label="Json"),
                        EnumVal(key="json_verbose", label="Json Verbose"),
                        EnumVal(key="video", label="Video"),
                    ],
                    default="json",
                )
            ),
        ],
    )

# Define input types
class DeepfakeDetectionInputs(TypedDict):
    video_paths: BatchFileInput  # Accepts multiple video file paths
    output_directory: DirectoryInput  # Accepts a directory path

class DeepfakeDetectionParameters(TypedDict):
    output_format: str

@server.route(
    "/detect_deepfake",
    task_schema_func=create_deepfake_detection_task_schema,
    short_title="Deepfake Detection",
    order=0
)
def detect_deepfake(inputs: DeepfakeDetectionInputs, parameters: DeepfakeDetectionParameters) -> ResponseBody:    
    # Initialize the VideoEvaluator with model and output paths
    output_path = inputs["output_directory"].path # Directory to save processed videos
    evaluator = VideoEvaluator(output_path=output_path)

    output_format = parameters["output_format"]
    verbose = output_format == "json_verbose"
    
    results = []

    if output_format in ["json", "json_verbose"]:
        # Collect all results in a dictionary
        all_results = {
            "analysis_results": [],
            "metadata": {
                "total_videos": len(inputs['video_paths'].files),
                "verbose_output": verbose,
            }
        }
        
        # Process each video and add its results to the dictionary
        for video_path in inputs['video_paths'].files:
            result = evaluator.evaluate_video(video_path.path, output_mode="json", verbose=verbose)
            if result is not None:
                all_results["analysis_results"].append({
                    "video_path": str(video_path.path),
                    "result": result
                })
            else:
                all_results["analysis_results"].append({
                    "video_path": str(video_path.path),
                    "result": None,
                    "error": "Processing failed"
                })

        # Save all results to a single JSON file
        json_filename = "deepfake_detection_results.json"
        json_path = os.path.join(output_path, json_filename)
        
        with open(json_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        # Return single JSON file response
        results.append(
            FileResponse(
                output_type=ResponseType.FILE,
                file_type=FileType.JSON,
                path=str(json_path),
                title="Deepfake Detection Results",
                subtitle=f"Analysis for {len(inputs['video_paths'].files)} videos"
            )
        )
    
    else:  # video output
        for video_path in inputs['video_paths'].files:
            processed_video_path = evaluator.evaluate_video(
                video_path.path,
                output_mode="video",
                verbose=False
            )
            
            if processed_video_path is not None:
                results.append(
                    FileResponse(
                        output_type=ResponseType.FILE,
                        file_type=FileType.VIDEO,
                        path=str(processed_video_path),
                        title=f"Processed {video_path.path}",
                        subtitle="Deepfake Detection Visualization"
                    )
                )
            else:
                print(f"Failed to process video: {video_path.path}")
            
    # Return the processed file paths as a BatchFileResponse
    return ResponseBody(
        root=BatchFileResponse(
            files=results
        )
    )

if __name__ == "__main__":
    # Run the server
    parser = argparse.ArgumentParser(description="Run a server.")
    parser.add_argument(
        "--port", type=int, help="Port number to run the server", default=5000
    )
    args = parser.parse_args()
    server.run(port=args.port)
