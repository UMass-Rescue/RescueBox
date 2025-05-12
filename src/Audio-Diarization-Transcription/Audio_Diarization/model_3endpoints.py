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
import whisper
from collections import defaultdict
from Audio_Diarization.utils import diarize_text
import typer
import csv
from typing import Optional
import sqlite3

# Load models
pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.0")

# To use local model
# PATH_TO_CONFIG = "./models/pyannotediarizationconfig.yaml"
# pipeline = load_pyannote_pipeline_from_pretrained(PATH_TO_CONFIG)
asr_model = whisper.load_model("medium.en")

class AudioTranscriptionDB:
    def __init__(self, db_path: str = r"src\Audio-Diarization-Transcription\Audio_Diarization\audio_transcriptions.db"):
        """Initialize a simple database for audio transcription results"""
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self) -> None:
        """Create a single table for all transcription results"""
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transcriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audio_file TEXT NOT NULL,
            speaker_id TEXT,
            transcription TEXT,
            segment_duration REAL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audio_file ON transcriptions(audio_file)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_speaker_id ON transcriptions(speaker_id)")
        self.conn.commit()

    def add_transcription(
        self,
        audio_file: str,
        speaker_id: Optional[str] = None,
        transcription: Optional[str] = None,
        segment_duration: Optional[float] = None
    ) -> int:
        """Add a transcription result to the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO transcriptions (
            audio_file, speaker_id, transcription, segment_duration
        ) VALUES (?, ?, ?, ?)
        """, (audio_file, speaker_id, transcription, segment_duration))
        self.conn.commit()
        return cursor.lastrowid

    def get_transcriptions(self, audio_file: Optional[str] = None) -> List[Dict]:
        """Get all transcriptions, optionally filtered by audio file"""
        cursor = self.conn.cursor()
        
        if audio_file:
            cursor.execute("""
            SELECT audio_file, speaker_id, transcription, segment_duration, processed_at
            FROM transcriptions
            WHERE audio_file = ?
            ORDER BY processed_at
            """, (audio_file,))
        else:
            cursor.execute("""
            SELECT audio_file, speaker_id, transcription, segment_duration, processed_at
            FROM transcriptions
            ORDER BY processed_at
            """)
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def close(self) -> None:
        """Close the database connection"""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class DiarizationInputs(TypedDict):
    input_dir: DirectoryInput
    output_dir: DirectoryInput


class DiarizationParameters(TypedDict):
    pass


class AudioInputs(TypedDict):
    input_dir: DirectoryInput
    output_dir: DirectoryInput


class AudioParameters(TypedDict):
    pass


def create_task_schema() -> TaskSchema:
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


def is_audio_file(file_path: Path) -> bool:
    audio_extensions = {".wav", ".mp3", ".flac", ".ogg"}
    return file_path.suffix.lower() in audio_extensions


# Format functions for different endpoints
def format_diarization_segments(
    segments: List[Dict[str, float]],
) -> Dict[str, List[str]]:
    """Format speaker segments for diarization-only endpoint"""
    speaker_segments = defaultdict(list)
    for segment in segments:
        speaker = segment["speaker"]
        start = f'{segment["start"]:.2f}'
        end = f'{segment["end"]:.2f}'
        speaker_segments[speaker].append(f"{start} - {end}")
    return dict(speaker_segments)


def format_transcription_only(asr_result: Dict) -> Dict[str, str]:
    """Format transcription for transcription-only endpoint"""
    return {"transcription": asr_result["text"]}


def format_combined_result(diarized_result) -> Dict[str, Dict[str, str]]:
    """Format combined diarization and transcription"""
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

def process_audio(
    inputs: AudioInputs,
    parameters: AudioParameters,
    mode: str = "diarize_and_transcribe" # Common for all
) -> None:
    input_path = Path(inputs["input_dir"].path)
    audio_files = [input_path] if input_path.is_file() else list(input_path.glob("*"))

    # Initialize the database
    with AudioTranscriptionDB() as db:
        for audio_file in audio_files:
            if not is_audio_file(audio_file):
                continue  # Skip non-audio files

            try:
                # Common variables
                diarization = None
                asr_result = None
                audio_file_str = str(audio_file)

                if mode in ["diarize", "diarize_and_transcribe"]:
                    diarization = pipeline(audio_file_str)

                if mode in ["transcribe", "diarize_and_transcribe"]:
                    asr_result = asr_model.transcribe(audio_file_str)

                # Handle different modes
                if mode == "diarize":
                    for turn, _, speaker in diarization.itertracks(yield_label=True):
                        db.add_transcription(
                            audio_file=audio_file_str,
                            speaker_id=speaker,
                            segment_duration=turn.end - turn.start
                        )

                elif mode == "transcribe":
                    db.add_transcription(
                        audio_file=audio_file_str,
                        transcription=asr_result["text"],
                        segment_duration=asr_result["segments"][-1]["end"] if asr_result["segments"] else 0
                    )

                elif mode == "diarize_and_transcribe":
                    aligned = diarize_text(asr_result, diarization)
                    for seg, spk, sent in aligned:
                        db.add_transcription(
                            audio_file=audio_file_str,
                            speaker_id=spk,
                            transcription=sent,
                            segment_duration=seg.end - seg.start
                        )

            except Exception as e:
                print(f"Error processing {audio_file.name}: {str(e)}")
                continue

def save_as_csv(data: dict, csv_path: Path):
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        first_item = next(iter(data.values())) 
        if "transcription" in first_item:
            writer.writerow(['Audio File', 'Transcription'])
            for audio_file, content in data.items():
                writer.writerow([audio_file, content['transcription']])
                

        elif isinstance(first_item, dict) and any(isinstance(v, dict) for v in first_item.values()):
            writer.writerow(['Audio File', 'Speaker', 'Time Range', 'Text'])

            for audio_file, speakers in data.items():
                for speaker, segments in speakers.items():
                    for time_range, text in segments.items():
                        writer.writerow([audio_file, speaker, time_range, text])
        else:
            writer.writerow(['Audio File', 'Speaker', 'Time Range'])
            for audio_file, speakers in data.items():
                for speaker, segments in speakers.items():
                    for segment in segments:
                        writer.writerow([audio_file, speaker, segment])




# Initialize server
APP_NAME = "Audio_Diarization"
ml_service = MLService(APP_NAME)
ml_service.add_app_metadata(
    plugin_name=APP_NAME,
    name="Speaker Diarization + Transcription",
    author="Christina, Swetha, Nikita",
    version="2.0",
    info="app-info.md",
)


# @server.route("/diarize", order=0, task_schema_func=create_task_schema, short_title="Speaker Diarization")


def cli_parser(arg: str) -> DiarizationInputs:
    parts = arg.strip().split()
    if len(parts) != 2:
        raise typer.BadParameter("Expected two arguments: <input_dir> <output_dir>")
    return {
        "input_dir": DirectoryInput(path=parts[0]),
        "output_dir": DirectoryInput(path=parts[1]),
    }


def param_parser(args):
    return {}


def diarize_only(inputs: AudioInputs, parameters: AudioParameters) -> ResponseBody:
    input_path = Path(inputs["input_dir"].path)
    output_path = Path(inputs["output_dir"].path)
    output_path.mkdir(parents=True, exist_ok=True)
    results = {}

    audio_files = [input_path] if input_path.is_file() else list(input_path.glob("*"))

    for audio_file in audio_files:
        if is_audio_file(audio_file):
            try:
                diarization = pipeline(str(audio_file))
                segments = []
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    segments.append(
                        {"speaker": speaker, "start": turn.start, "end": turn.end}
                    )
                results[audio_file.name] = format_diarization_segments(segments)
            except Exception as e:
                results[audio_file.name] = f"Error: {str(e)}"
        else:
            results[audio_file.name] = "Error: Not a valid audio file"
    process_audio(inputs, parameters, mode="diarize_and_transcribe")
    csv_file = output_path / "diarize_output.csv"
    save_as_csv(results, csv_file)
    return ResponseBody(FileResponse(path=str(csv_file), file_type="csv"))


ml_service.add_ml_service(
    rule="/diarize",
    ml_function=diarize_only,
    inputs_cli_parser=typer.Argument(..., parser=cli_parser),
    parameters_cli_parser=typer.Argument(..., parser=param_parser),
    short_title="Diarization Only",
    order=0,
    task_schema_func=create_task_schema,
)


# @server.route("/transcribe", order=1, task_schema_func=create_task_schema, short_title="Audio Transcription")
def transcribe_only(inputs: AudioInputs, parameters: AudioParameters) -> ResponseBody:
    input_path = Path(inputs["input_dir"].path)
    output_path = Path(inputs["output_dir"].path)
    output_path.mkdir(parents=True, exist_ok=True)
    results = {}

    audio_files = [input_path] if input_path.is_file() else list(input_path.glob("*"))

    for audio_file in audio_files:
        if is_audio_file(audio_file):
            try:
                asr_result = asr_model.transcribe(str(audio_file))
                results[audio_file.name] = format_transcription_only(asr_result)
            except Exception as e:
                results[audio_file.name] = f"Error: {str(e)}"
        else:
            results[audio_file.name] = "Error: Not a valid audio file"
    process_audio(inputs, parameters, mode="diarize_and_transcribe")
    csv_file = output_path / "transcribe_output.csv"
    save_as_csv(results, csv_file)
    return ResponseBody(FileResponse(path=str(csv_file), file_type="csv"))


ml_service.add_ml_service(
    rule="/transcribe",
    ml_function=transcribe_only,
    inputs_cli_parser=typer.Argument(..., parser=cli_parser),
    parameters_cli_parser=typer.Argument(..., parser=param_parser),
    short_title="Transcription Only",
    order=1,
    task_schema_func=create_task_schema,
)


# @server.route("/diarize-transcribe", order=2, task_schema_func=create_task_schema, short_title="Speaker Diarization + Transcription")
def diarize_and_transcribe(
    inputs: AudioInputs, parameters: AudioParameters
) -> ResponseBody:
    input_path = Path(inputs["input_dir"].path)
    output_path = Path(inputs["output_dir"].path)
    output_path.mkdir(parents=True, exist_ok=True)
    results = {}

    audio_files = [input_path] if input_path.is_file() else list(input_path.glob("*"))

    for audio_file in audio_files:
        if is_audio_file(audio_file):
            try:
                diarization = pipeline(str(audio_file))
                asr_result = asr_model.transcribe(str(audio_file))
                aligned = diarize_text(asr_result, diarization)
                results[audio_file.name] = format_combined_result(aligned)
            except Exception as e:
                results[audio_file.name] = f"Error: {str(e)}"
        else:
            results[audio_file.name] = "Error: Not a valid audio file"
    process_audio(inputs, parameters, mode="diarize_and_transcribe")
    csv_file = output_path / "diarize_and_transcribe_output.csv"
    save_as_csv(results, csv_file)
    return ResponseBody(FileResponse(path=str(csv_file), file_type="csv"))


ml_service.add_ml_service(
    rule="/diarize_and_transcribe",
    ml_function=diarize_and_transcribe,
    inputs_cli_parser=typer.Argument(..., parser=cli_parser),
    parameters_cli_parser=typer.Argument(..., parser=param_parser),
    short_title="Diarization and Trancription",
    order=2,
    task_schema_func=create_task_schema,
)

app = ml_service.app

if __name__ == "__main__":
    app()
