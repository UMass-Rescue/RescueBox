import os
import typer
from typing import Annotated
from typing import TypedDict

app = typer.Typer()

# Define input types
class DeepfakeDetectionInputs(TypedDict):
    video_paths: str  # Accepts multiple video file paths
    output_directory: str  # Accepts a directory path

class DeepfakeDetectionParameters(TypedDict):
    cuda: str

class VideoEvaluator:
    def __init__(self, model_path=None, output_path='.', cuda=True):
        self.output_path = output_path
        self.cuda = cuda

    def evaluate_video(self, video_path, start_frame=0, end_frame=None):
        print(f'Starting: {video_path}')
        video_fn = f"{os.path.splitext(os.path.basename(video_path))[0]}_processed.avi"
        processed_video_path = os.path.join(self.output_path, video_fn)
        os.makedirs(self.output_path, exist_ok=True)
        return processed_video_path

@app.command
def detect_deepfake(
    # inputs: DeepfakeDetectionInputs, parameters: DeepfakeDetectionParameters    
    # Initialize the VideoEvaluator with model and output paths
    video_paths: str = typer.Argument(..., help="The path to input video files eg: path/to/your/video.folder"),
    model_path: str = typer.Argument(..., help="The path to the pre-trained model eg: path/to/your/model.pth"),
    output_path: str = typer.Argument(..., help="The path Directory to save processed videos"),
    cuda_flag: str = Annotated[bool, typer.Option("-cuda",help="cuda flag boolean")] == "True"
                               ) -> str:
    evaluator = VideoEvaluator(model_path=model_path, output_path=output_path, cuda=cuda_flag)
    
    # Process each video file path and store the output paths
    output_paths = []
    for video_path in video_paths.files:
        # Run the evaluation
        processed_video_path = evaluator.evaluate_video(video_path.path)

        if processed_video_path is not None:
            # Construct FileResponse with required fields
            output_paths.append(processed_video_path)
        else:
            # Handle the case where processed_video_path is None
            print(f"Failed to process video: {video_path.path}")
    # Process each video file path and store the output path
    return output_paths

''''

@app.command()
def open() -> str:
    """
    Open docs in the browser
    """
    typer.launch(DOCS_GITHUB_URL)
    return DOCS_GITHUB_URL


@app.command()
def ask(
    question: str = typer.Argument(..., help="Ask a question against the docs"),
) -> str:
    """
    Ask a question against the docs
    """
    reference_doc = download_reference_doc()
    chat_config = load_chat_config()
    chat_config["prompt"]["system"] = chat_config["prompt"]["system"].format(
        reference_doc=reference_doc
    )

    return stream_output(question, chat_config)
'''