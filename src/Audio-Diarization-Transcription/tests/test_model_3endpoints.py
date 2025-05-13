from pathlib import Path
from unittest.mock import patch

from rb.lib.common_tests import RBAppTest
from rb.api.models import AppMetadata
from Audio_Diarization.model_3endpoints import app as cli_app, APP_NAME, create_task_schema



class TestAudioDiarization(RBAppTest):
    def setUp_method(self):
        self.set_app(cli_app, APP_NAME)

    def get_metadata(self):
        return AppMetadata(
            plugin_name=APP_NAME,
            name="Speaker Diarization + Transcription",
            author="Christina, Swetha, Nikita",
            version="2.0",
            info="app-info.md",
        )

    def get_all_ml_services(self):
        return [
            (0, "diarize", "Diarization Only", create_task_schema()),
            (1, "transcribe", "Transcription Only", create_task_schema()),
            (2, "diarize_and_transcribe", "Diarization and Trancription", create_task_schema()),
        ]
    

    @patch("Audio_Diarization.model_3endpoints.diarize_only", return_value="Mocked summary")
    def test_diarize_only_command(self, summarize_mock, ensure_model_exists_mock):
        diarize_api = f"/{APP_NAME}/Audio_Diarization/model_3endpoints"
        full_path = Path.cwd() / "src" / "Audio-Diarization-Transcription"/ "Audio_Diarization" / "input"
        output_path = Path.cwd() / "src" / "Audio-Diarization-Transcription"/ "Audio_Diarization" / "output"
        input_str = f"{str(full_path)},{str(output_path)}"
        parameter_str = " "
        result = self.runner.invoke(
            self.cli_app, [diarize_api, input_str, parameter_str]
        )
        assert result.exit_code == 0, f"Error: {result.output}"
        output_files = list(output_path.glob("*.csv"))
        assert len(output_files) == 1
        for file in output_files:
            with open(file, "r") as f:
                content = f.read()
                assert "Mocked summary" == content

