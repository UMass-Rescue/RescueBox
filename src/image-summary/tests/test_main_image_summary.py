from image_summary.main import app as cli_app, APP_NAME, task_schema, server
from rb.lib.common_tests import RBAppTest
from pathlib import Path
from unittest.mock import patch
from image_summary.process import SUPPORTED_IMAGE_EXTENSIONS, iter_image_files
import json


def _mock_process_images(model, input_dir, output_dir, file_filter):
    """Write one mocked .txt per image without calling Ollama."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    ff = list(file_filter) if file_filter else []
    pairs = []
    for image_path in iter_image_files(input_path, ff):
        out_file = output_path / (image_path.name + ".txt")
        out_file.write_text("Mocked summary", encoding="utf-8")
        pairs.append(
            {
                "input_path": str(image_path.resolve()),
                "output_path": str(out_file.resolve()),
            }
        )
    return pairs


class TestImageSummary(RBAppTest):
    def setup_method(self):
        self.set_app(cli_app, APP_NAME)

    def get_metadata(self):
        assert server._app_metadata is not None
        return server._app_metadata

    def get_all_ml_services(self):
        return [
            (0, "summarize-images", "Describe Images", task_schema()),
        ]

    @patch("image_summary.model.ensure_model_exists")
    @patch(
        "image_summary.main.process_images",
        side_effect=_mock_process_images,
    )
    def test_summarize_images_command(
        self, process_images_mock, ensure_model_exists_mock
    ):
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

    @patch("image_summary.model.ensure_model_exists")
    @patch(
        "image_summary.main.process_images",
        side_effect=_mock_process_images,
    )
    def test_api_summarize(self, process_images_mock, ensure_model_exists_mock):
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
        parsed = json.loads(body["value"])
        assert isinstance(parsed, dict)
        assert parsed.get("image_summary") is True
        assert "input_dir" in parsed
        results = parsed["files"]
        assert results is not None
        assert len(results) == len(expected_files)
        assert set(expected_files) == set(results)
        for file in results:
            assert file.endswith(".txt")
        pairs = parsed.get("file_pairs")
        assert isinstance(pairs, list)
        assert len(pairs) == len(expected_files)
        by_out = {
            p["output_path"]: p["input_path"] for p in pairs if isinstance(p, dict)
        }
        for ef in expected_files:
            assert ef in by_out
            assert (
                by_out[ef]
                .lower()
                .endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff"))
            )

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
