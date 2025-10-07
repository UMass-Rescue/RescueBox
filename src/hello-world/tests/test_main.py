from pathlib import Path

from rb.api.models import ResponseBody
from hello_world.main import app as cli_app, APP_NAME, task_schema
from rb.lib.common_tests import RBAppTest
from rb.api.models import AppMetadata


class TestHelloWorld(RBAppTest):
    def setup_method(self):
        self.set_app(cli_app, APP_NAME)

    def get_metadata(self):
        return AppMetadata(
            plugin_name=APP_NAME,
            name="Hello World",
            author="Gemini",
            version="0.1.0",
            info="A simple Hello World plugin for RescueBox.",
        )

    def get_all_ml_services(self):
        return [
            (0, "hello", "Hello World", task_schema()),
        ]

    def test_cli_hello_command(self, tmp_path, caplog):
        input_file = tmp_path / "input.txt"
        input_file.write_text("test")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with caplog.at_level("INFO"):
            input_args = f"{str(input_file)},{str(output_dir)}"
            result = self.runner.invoke(self.cli_app, [f"/{APP_NAME}/hello",input_args])
            assert result.exit_code == 0
            assert any("Successfully wrote 'Hello World'" in message for message in caplog.messages)

    def test_api_hello_command(self, tmp_path):
        input_file = tmp_path / "input.txt"
        input_file.write_text("test")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        input_json = {
            "inputs": {
                "input_file": {"path": str(input_file)},
                "output_dir": {"path": str(output_dir)},
            }
        }
        response = self.client.post(f"/{APP_NAME}/hello", json=input_json)
        assert response.status_code == 200
        body = ResponseBody(**response.json())
        assert body.root.value and "Successfully wrote 'Hello World'" in body.root.value
