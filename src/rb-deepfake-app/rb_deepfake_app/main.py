import os
from typing import Annotated, Optional, List, Dict
from typing_extensions import TypedDict
from flask_ml.flask_ml_server.models import (
    BatchFileInput,
    FileInput,
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
import typer
from rb_deepfake_app.video_evaluator import VideoEvaluator
import pdb
import json
import logging
import requests
from pprint import pprint
from fastapi import APIRouter, Depends


plugin_router = APIRouter()

app = typer.Typer()

logger = logging.getLogger("uvicorn.error")
logger.propagate = True
logger.setLevel(logging.DEBUG)

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
            )
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
            )
        ]
    )

# Define input types
class DeepfakeDetectionInputs(TypedDict):
    video_paths: Optional[BatchFileInput] = None # Accepts multiple video file paths
    output_directory: Optional[DirectoryInput] = None # Accepts a directory path

class DeepfakeDetectionParameters(TypedDict):
    output_format: Optional[str] = None

'''

    inputs: Annotated[Optional[DeepfakeDetectionInputs], 
                      typer.Argument(default={"video_paths": "/tmp",
                               "output_directory" : "/tmp"},
                                help="The path to inputs")]  = {"video_paths": "/tmp",
                               "output_directory" : "/tmp"},
    parameters: Annotated[Optional[DeepfakeDetectionParameters], 
                          typer.Argument(default={"output_format": "xx"},
         help="The path to params")]  = {"notused"},
'''

def show_json(path: str):
    if not os.path.exists(path):
        print(f"Path {path} does not exist")
        raise typer.Abort()
    with open(path, "r") as f:
        for line in f:
            print(line)

@app.command()
def run_deepfake(
    video_paths: str = typer.Argument(
        str, help="The path to input video files eg: path/to/your/video.folder"
    ),
    output_directory: str = typer.Argument(
        str, help="The path to output video files eg: path/to/out/video.folder"
    ),
    output_format: str = typer.Argument(
        str, help="The output format eg:json"
    )
)-> str:
    fi = FileInput(path = video_paths)
    
    vp = BatchFileInput( files= [fi])
    
    od = DirectoryInput( path = output_directory)

    df = DeepfakeDetectionInputs(video_paths=vp, output_directory=od)

    of = DeepfakeDetectionParameters(output_format= output_format)
    pprint(df)
    # pack multiple function args into one dict
    dt = {"inputs": df, "parameters": of}

    response = requests.get("http://localhost:8000/run/",  data = json.dumps(dt, default=vars),headers={'Content-Type': 'application/json'})
    response_dict = response.json() 
    outfile = { "output_json": "not available"}
    if response_dict["files"][0] is not None:
        pprint("title: " + response_dict["files"][0]["title"])
        pprint("path: " + response_dict["files"][0]["path"])
        outfile = response_dict["files"][0]["path"]
        #dto = { "path" : outfile}
    show_json(outfile)
    return json.dumps(outfile)

@plugin_router.get("/run/")
def detect_deepfake(inputs: DeepfakeDetectionInputs, parameters: DeepfakeDetectionParameters
) -> ResponseBody:

    output_path = inputs["output_directory"].path # Directory to save processed videos
    evaluator = VideoEvaluator(output_path=output_path)
    # Process each video file path and store the output paths

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
            logger.debug(pprint(video_path))
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


# @app.command()
# def test(name: str) -> str:
#     print(f"Hello world {name}")
#     return True
