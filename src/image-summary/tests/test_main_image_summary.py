from image_summary.main import app as cli_app, APP_NAME, task_schema
from rb.lib.common_tests import RBAppTest
from rb.api.models import AppMetadata
from pathlib import Path
from unittest.mock import patch
from image_summary.process import SUPPORTED_IMAGE_EXTENSIONS
import json


class TestImageSummary(RBAppTest):
    def setup_method(self):
        self.set_app(cli_app, APP_NAME)

    def get_metadata(self):
        return AppMetadata(
            name="Image Summary",
            author="UMass Rescue",
            version="1.0.0",
            info=(
                "This plugin lets you generate rich descriptions for every image in a folder. "
                "For each image, it identifies the scene and setting, key objects and their attributes (colors, counts, positions), "
                "people and actions (if present), visible text (quoted verbatim), and notable visual details like lighting and composition. "
                "Input: a directory of images. Output: a matching directory of .txt files (one per image) containing the description."
            ),
            plugin_name=APP_NAME,
        )

    def get_all_ml_services(self):
        return [
            (0, "summarize-images", "Describe Images", task_schema()),
        ]

    @patch("image_summary.process.ensure_model_exists")
    @patch("image_summary.process.describe_image", return_value="Mocked summary")
    def test_summarize_images_command(self, describe_mock, ensure_model_exists_mock):
        summarize_api = f"/{APP_NAME}/summarize-images"
        full_path = Path.cwd() / "src" / "image-summary" / "test_input"
        output_path = Path.cwd() / "src" / "image-summary" / "test_output"
        # Clean any prior outputs
        output_path.mkdir(parents=True, exist_ok=True)
        for f in output_path.glob("*.txt"):
            try:
                f.unlink()
            except Exception:
                pass
        input_str = f"{str(full_path)},{str(output_path)}"
        parameter_str = "gemma3:4b"

        result = self.runner.invoke(
            self.cli_app, [summarize_api, input_str, parameter_str]
        )
        assert result.exit_code == 0, f"Error: {result.output}"

        input_files = [
            f
            for f in full_path.glob("*")
            if f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        ]
        # Expected output keeps original filename (with extension) and then appends .txt
        expected_files = {
            str(output_path / (file.name + ".txt")) for file in input_files
        }

        output_files = list(output_path.glob("*.txt"))
        assert len(output_files) == len(expected_files)
        assert set(map(str, output_files)) == expected_files
        for file in output_files:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                assert "Mocked summary" == content

    @patch("image_summary.process.ensure_model_exists")
    @patch("image_summary.process.describe_image", return_value="Mocked summary")
    def test_api_summarize(self, describe_mock, ensure_model_exists_mock):
        summarize_api = f"/{APP_NAME}/summarize-images"
        full_path = Path.cwd() / "src" / "image-summary" / "test_input"
        output_path = Path.cwd() / "src" / "image-summary" / "test_output"
        parameter_str = "gemma3:4b"
        input_json = {
            "inputs": {
                "input_dir": {"path": str(full_path)},
                "output_dir": {"path": str(output_path)},
            },
            "parameters": {"model": parameter_str},
        }
        response = self.client.post(summarize_api, json=input_json)
        assert response.status_code == 200
        body = response.json()
        input_files = [
            f
            for f in full_path.glob("*")
            if f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        ]
        expected_files = [
            str(output_path / (str(file.name) + ".txt")) for file in input_files
        ]
        results = json.loads(body["value"])
        assert results is not None
        assert len(results) == len(expected_files)
        assert set(expected_files) == set(results)
        for file in results:
            assert file.endswith(".txt")

    @patch("image_summary.process.ensure_model_exists")
    def test_invalid_path(self, ensure_model_exists_mock):
        summarize_api = f"/{APP_NAME}/summarize-images"
        bad_path = Path.cwd() / "src" / "image-summary" / "bad_tests"
        input_str = f"{str(bad_path)},{str(bad_path)}"
        parameter_str = "gemma3:4b"
        result = self.runner.invoke(
            self.cli_app, [summarize_api, input_str, parameter_str]
        )
        assert result.exit_code != 0
