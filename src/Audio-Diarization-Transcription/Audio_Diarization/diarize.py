from typing import TypedDict, Dict, List
from pathlib import Path
from rb.lib.ml_service import MLService
from rb.api.models import (
    DirectoryInput,
    FileResponse,
    InputSchema,
    InputType,
    ResponseBody,
    TaskSchema,
)
from pyannote.audio import Pipeline
import json
from collections import defaultdict

# Load the pre-trained speaker diarization pipeline
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0")


class DiarizationInputs(TypedDict):
    input_dir: DirectoryInput
    output_dir: DirectoryInput


class DiarizationParameters(TypedDict):
    pass


# Specifies the input and output directory
def create_diarization_task_schema() -> TaskSchema:
    input_schema = InputSchema(
        key="input_dir",
        label="Path to the directory containing audio files",
        input_type=InputType.DIRECTORY,
    )
    output_schema = InputSchema(
        key="output_dir",
        label="Path to the output directory",
        input_type=InputType.DIRECTORY,
    )
    return TaskSchema(inputs=[input_schema, output_schema], parameters=[])


# Formats the output in the JSON
def format_segments(segments: List[Dict[str, float]]) -> Dict[str, List[str]]:
    """Format speaker segments into the desired output format."""
    speaker_segments = defaultdict(list)

    for segment in segments:
        speaker = segment["speaker"]
        start = f'{segment["start"]:.2f}'
        end = f'{segment["end"]:.2f}'
        speaker_segments[speaker].append(f"{start} - {end}")

    # Convert defaultdict to regular dict and format the output
    formatted_output = {}
    for speaker, times in speaker_segments.items():
        formatted_output[speaker] = "  ".join(times)

    return formatted_output


# Create a server instance
server = MLService(__name__)

server.add_app_metadata(
    name="Speaker Diarization",
    author="Christina. Swetha, Nikita",
    version="1.0",
    info="app-info.md",
)


# Checks audio file types
def is_audio_file(file_path: Path) -> bool:
    """Check if a file is an audio file based on its extension."""
    audio_extensions = {".wav", ".mp3", ".flac", ".ogg"}
    return file_path.suffix.lower() in audio_extensions


@server.route(
    "/diarize",
    task_schema_func=create_diarization_task_schema,
    short_title="Speaker separation and transcription",
)
def diarize(
    inputs: DiarizationInputs, parameters: DiarizationParameters
) -> ResponseBody:
    input_path = Path(inputs["input_dir"].path)
    output_path = Path(inputs["output_dir"].path)
    output_path.mkdir(
        parents=True, exist_ok=True
    )  # Create output directory if it doesn't exist

    results = {}

    if input_path.is_file():
        # Process a single file
        if is_audio_file(input_path):
            diarization = pipeline(str(input_path))
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append(
                    {"speaker": speaker, "start": turn.start, "end": turn.end}
                )
            # Format the segments into the desired output
            results[input_path.name] = format_segments(segments)
        else:
            results[input_path.name] = "Error: Not a valid audio file"
    else:
        # Process all audio files in the input directory
        for input_file in input_path.glob("*"):
            if input_file.is_file() and is_audio_file(input_file):
                diarization = pipeline(str(input_file))
                segments = []
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    segments.append(
                        {"speaker": speaker, "start": turn.start, "end": turn.end}
                    )
                results[input_file.name] = format_segments(segments)

    # Save results to a JSON file in the specified output directory
    output_file = output_path / "output.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=4)

    return ResponseBody(FileResponse(path=str(output_file), file_type="json"))


if __name__ == "__main__":
    server.run()
