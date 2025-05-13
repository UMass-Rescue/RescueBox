import pytest
from pathlib import Path
from unittest import mock
from Audio_Diarization.model_3endpoints import (
    diarize_only,
    transcribe_only,
    diarize_and_transcribe,
    AudioTranscriptionDB,
    AudioInputs,
    AudioParameters,
)
from rb.api.models import DirectoryInput


@pytest.fixture
def temp_dirs(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    return input_dir, output_dir


@pytest.fixture
def dummy_audio_file(temp_dirs):
    input_dir, _ = temp_dirs
    dummy_audio = input_dir / "test.wav"
    dummy_audio.write_bytes(b"dummy audio content")
    return dummy_audio


@pytest.fixture
def mock_pipeline():
    with mock.patch("Audio_Diarization.model_3endpoints.pipeline") as mocked_pipeline:
        mocked_pipeline.return_value.return_value = mock.Mock()
        mocked_pipeline.return_value.itertracks.return_value = [
            (mock.Mock(start=0.0, end=1.0), None, "Speaker 1")
        ]
        yield mocked_pipeline


@pytest.fixture
def mock_asr_model():
    with mock.patch("Audio_Diarization.model_3endpoints.asr_model") as mocked_asr:
        mocked_asr.transcribe.return_value = {
            "text": "This is a test transcription.",
            "segments": [{"end": 1.0}],
        }
        yield mocked_asr


@pytest.fixture(autouse=True)
def mock_process_audio():
    with mock.patch("Audio_Diarization.model_3endpoints.process_audio") as mocked:
        yield mocked


def make_inputs(input_dir, output_dir):
    return AudioInputs(
        input_dir=DirectoryInput(path=str(input_dir)),
        output_dir=DirectoryInput(path=str(output_dir)),
    )


def test_diarize_only(temp_dirs, dummy_audio_file, mock_pipeline):
    input_dir, output_dir = temp_dirs
    inputs = make_inputs(input_dir, output_dir)
    parameters = AudioParameters()

    response = diarize_only(inputs, parameters)

    output_csv = Path(response.root.path)
    assert output_csv.exists()
    assert output_csv.name == "diarize_output.csv"


def test_transcribe_only(temp_dirs, dummy_audio_file, mock_asr_model):
    input_dir, output_dir = temp_dirs
    inputs = make_inputs(input_dir, output_dir)
    parameters = AudioParameters()

    response = transcribe_only(inputs, parameters)

    output_csv = Path(response.root.path)
    assert output_csv.exists()
    assert output_csv.name == "transcribe_output.csv"


def test_diarize_and_transcribe(
    temp_dirs,
    dummy_audio_file,
    mock_pipeline,
    mock_asr_model,
):
    with mock.patch(
        "Audio_Diarization.model_3endpoints.diarize_text"
    ) as mock_diarize_text:
        mock_diarize_text.return_value = [
            (mock.Mock(start=0.0, end=1.0), "Speaker 1", "Hello world")
        ]

        input_dir, output_dir = temp_dirs
        inputs = make_inputs(input_dir, output_dir)
        parameters = AudioParameters()

        response = diarize_and_transcribe(inputs, parameters)

        output_csv = Path(response.root.path)
        assert output_csv.exists()
        assert output_csv.name == "diarize_and_transcribe_output.csv"


def test_audio_transcription_db(tmp_path):
    # Use a temporary SQLite database
    db_path = tmp_path / "test_transcriptions.db"

    # Open DB in a context manager
    with AudioTranscriptionDB(str(db_path)) as db:
        # Add a mock transcription entry
        row_id = db.add_transcription(
            audio_file="test.wav",
            speaker_id="Speaker 1",
            transcription="Hello world",
            segment_duration=1.23,
        )

        assert isinstance(row_id, int)

        # Fetch inserted data
        results = db.get_transcriptions("test.wav")
        assert len(results) == 1

        row = results[0]
        assert row["audio_file"] == "test.wav"
        assert row["speaker_id"] == "Speaker 1"
        assert row["transcription"] == "Hello world"
        assert abs(row["segment_duration"] - 1.23) < 1e-5
