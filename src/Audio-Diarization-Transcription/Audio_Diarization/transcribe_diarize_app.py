from typing import TypedDict, Dict
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

# Speaker Diarization and audio cropping
from pyannote.audio import Pipeline
from pyannote.core import Segment
from pyannote.audio import Audio
import whisper # Audio trancription
import json # Outputs into JSON format
from Audio_Diarization.utils import diarize_text, load_pyannote_pipeline_from_pretrained  # Custom helper that aligns Whisper transcription with diarization

# Load models
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0")

#To use local model
#PATH_TO_CONFIG = "./models/pyannote_diarization_config.yaml"
#pipeline = load_pyannote_pipeline_from_pretrained(PATH_TO_CONFIG)
asr_model = whisper.load_model("medium.en")

class DiarizationInputs(TypedDict):
    input_dir: DirectoryInput
    output_dir: DirectoryInput

class DiarizationParameters(TypedDict):
    pass

def create_task_schema() -> TaskSchema:
    input_schema = InputSchema(
        key="input_dir",
        label="Path to the directory containing audio files",
        input_type=InputType.DIRECTORY
    )
    output_schema = InputSchema(
        key="output_dir",
        label="Path to the output directory",
        input_type=InputType.DIRECTORY
    )
    return TaskSchema(
        inputs=[input_schema, output_schema],
        parameters=[]
    )

# Checks audio file types
def is_audio_file(file_path: Path) -> bool:
    audio_extensions = {".wav", ".mp3", ".flac", ".ogg"}
    return file_path.suffix.lower() in audio_extensions

# Format by speaker lable followed by timestamps and transcription in a dictionary
def format_transcription(diarized_result) -> Dict[str, Dict[str, str]]:
    output = {}
    speaker_segments = {}

    for seg, spk, sent in diarized_result:
        if spk not in speaker_segments:
            speaker_segments[spk] = []
        speaker_segments[spk].append((seg.start, seg.end, sent))

    for speaker, segments in speaker_segments.items():
        speaker_dict = {}
        for start, end, text in segments:
            time_range = f"{start:.1f}-{end:.1f}"
            speaker_dict[time_range] = text
        output[speaker] = speaker_dict

    return output

# Server
server = MLService(__name__)
server.add_app_metadata(
    name="Speaker Diarization + Transcription",
    author="Christina, Swetha, Nikita",
    version="2.0",
    info="app-info.md"
)

@server.route("/diarize-transcribe", task_schema_func=create_task_schema, short_title="Speaker Diarization + Transcription")
def diarize_and_transcribe(inputs: DiarizationInputs, parameters: DiarizationParameters) -> ResponseBody:
    input_path = Path(inputs["input_dir"].path)
    output_path = Path(inputs["output_dir"].path)
    output_path.mkdir(parents=True, exist_ok=True)

    results = {}

    audio_files = [input_path] if input_path.is_file() else list(input_path.glob("*"))

    for audio_file in audio_files:
        if is_audio_file(audio_file):
            try:
                print(f"Processing {audio_file.name}...")
                diarization = pipeline(str(audio_file))  # diarization
                asr_result = asr_model.transcribe(str(audio_file)) # transcription
                aligned = diarize_text(asr_result, diarization)          # align speaker label with text
                results[audio_file.name] = format_transcription(aligned) # format result by speaker
            except Exception as e:
                results[audio_file.name] = f"Error: {str(e)}"
        else:
            results[audio_file.name] = "Error: Not a valid audio file"

    output_file = output_path / "output.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    return ResponseBody(FileResponse(path=str(output_file), file_type="json"))

if __name__ == "__main__":
    server.run()
