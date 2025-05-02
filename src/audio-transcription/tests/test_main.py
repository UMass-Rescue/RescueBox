import json
from pathlib import Path

from rb.api.models import ResponseBody
from audio_transcription.main import app as cli_app, APP_NAME, task_schema
from rb.lib.common_tests import RBAppTest
from rb.api.models import AppMetadata


class TestAudioTranscription(RBAppTest):
    def setup_method(self):
        self.set_app(cli_app, APP_NAME)

    def get_metadata(self):
        return AppMetadata(
            plugin_name=APP_NAME,
            name="Audio Transcription",
            author="RescueBox Team",
            version="2.0.0",
            info="A parser for transcribing audio files.",
        )

    def get_all_ml_services(self):
        return [
            (0, "transcribe", "Transcribe audio files", task_schema()),
        ]

    def test_negative_test(self):
        transcribe_api = f"/{APP_NAME}/transcribe"
        bad_path = Path.cwd() / "src" / "audio-transcription" / "bad_tests"
        result = self.runner.invoke(cli_app, [transcribe_api, str(bad_path)])
        assert "Aborted" in result.stdout or result.exit_code != 0

    def test_cli_transcribe_command(self, caplog):
        with caplog.at_level("INFO"):
            transcribe_api = f"/{APP_NAME}/transcribe"
            full_path = Path.cwd() / "src" / "audio-transcription" / "tests"
            print(f"Full path: {full_path}")
            print(f"Transcribe API: {transcribe_api}")
            result = self.runner.invoke(cli_app, [transcribe_api, str(full_path)])
            assert result.exit_code == 0
            expected_transcript = "Twinkle twinkle little star"
            assert any(expected_transcript in message for message in caplog.messages)

    def test_api_transcribe_command(self):
        transcribe_api = f"/{APP_NAME}/transcribe"
        full_path = Path.cwd() / "src" / "audio-transcription" / "tests"
        input_json = {
            "inputs": {
                "input_dir": {
                    "path": str(full_path),
                }
            }
        }
        response = self.client.post(transcribe_api, json=input_json)
        assert response.status_code == 200
        body = ResponseBody(**response.json())
        assert body.root.texts and "Twinkle" in body.root.texts[0].value

    def test_negative_api_transcribe_command(self):
        """pass in valid directory but no audio files , expect 422 validation error"""
        transcribe_api = f"/{APP_NAME}/transcribe"
        full_path = Path.cwd() / "src" / "audio-transcription" / "tests" / "negative"
        input_json = {
            "inputs": {
                "input_dir": {
                    "path": str(full_path),
                }
            }
        }
        response = self.client.post(transcribe_api, json=input_json)
        assert response.status_code == 422
        resp = json.loads(json.dumps(response.json()))
        print(f"Response: {resp["detail"]["error"]}")
        assert resp and "No file extensions matching" in resp["detail"]["error"]
