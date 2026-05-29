import logging
from pathlib import Path
from unittest.mock import patch
import pytest
from deepfake_detection.main import (
    app as cli_app,
    APP_NAME,
    create_transform_case_task_schema as task_schema,
    app_info,
)
from rb.api.models import AppMetadata, BatchFileResponse, ResponseBody
from rb.lib.common_tests import RBAppTest


class TestDeepFakeServer(RBAppTest):
    def setup_method(self):
        # Skip heavy model tests when ONNX artifacts are not available in the workspace.
        models_dir = Path("src/deepfake-detection/deepfake_detection/onnx_models")
        if not models_dir.exists():
            pytest.skip("Deepfake ONNX models not available in CI environment")
        self.set_app(cli_app, APP_NAME)

    def get_metadata(self):
        print(APP_NAME)
        return AppMetadata(
            name="Detect DeepFakes",
            author="UMass RescueLab",
            version="3.0.0",
            info=app_info,
            plugin_name=APP_NAME,
            gpu=True,
        )

    def get_all_ml_services(self):
        return [
            (0, "predict", "DeepFake Detection", task_schema()),
        ]

    @patch("deepfake_detection.main.defaultDataset")
    @patch("deepfake_detection.main.run_models")
    def test_cli_predict(self, run_models_mock, defaultDataset_mock, caplog, tmp_path):
        caplog.set_level(logging.INFO)
        # Prepare a dummy image and mock predictions
        dummy_image = tmp_path / "img1.jpg"
        dummy_image.write_text("dummy")
        run_models_mock.return_value = [
            [
                {"model_name": "TestModel"},
                {
                    "image_path": str(dummy_image),
                    "prediction": "fake",
                    "confidence": 1.0,
                },
            ]
        ]
        # Set up input/output directories
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "img1.jpg").write_text("dummy")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        predict_api = f"/{APP_NAME}/predict"
        inputs_str = f"{str(input_dir)},{str(output_dir)}"
        parameters_str = "all"
        result = self.runner.invoke(cli_app, [predict_api, inputs_str, parameters_str])
        assert result.exit_code == 0, f"CLI failed: {result.output}"

        # Verify a CSV was created and contains our mock data
        csv_files = list(output_dir.glob("predictions_*.csv"))
        assert len(csv_files) == 1
        content = csv_files[0].read_text()
        assert "TestModel" in content
        assert "fake" in content

    def test_invalid_path(self):
        predict_api = f"/{APP_NAME}/predict"
        bad_dir = Path("nonexistent_dir")
        inputs_str = f"{str(bad_dir)},{str(bad_dir)}"
        parameters_str = "all"
        result = self.runner.invoke(cli_app, [predict_api, inputs_str, parameters_str])
        assert result.exit_code != 0

    @patch("deepfake_detection.main.defaultDataset")
    @patch("deepfake_detection.main.run_models")
    def test_api_predict(self, run_models_mock, defaultDataset_mock, tmp_path):
        # Prepare a dummy image and mock predictions
        dummy_image = tmp_path / "img1.jpg"
        dummy_image.write_text("dummy")
        run_models_mock.return_value = [
            [
                {"model_name": "TestModel"},
                {
                    "image_path": str(dummy_image),
                    "prediction": "fake",
                    "confidence": 1.0,
                },
            ]
        ]
        # Set up input/output directories
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "img1.jpg").write_text("dummy")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        predict_api = f"/{APP_NAME}/predict"
        payload = {
            "inputs": {
                "input_dir": {"path": str(input_dir)},
                "output_dir": {"path": str(output_dir)},
            },
            "parameters": {
                "facecrop": "false",
            },
        }
        response = self.client.post(predict_api, json=payload)
        assert response.status_code == 200
        body = ResponseBody(**response.json())
        batch = body.root
        assert isinstance(batch, BatchFileResponse)
        assert len(batch.files) == 1
        assert batch.files[0].metadata is not None
        assert batch.files[0].metadata.get("Prediction") == "fake"
        csv_files = list(output_dir.glob("predictions_*.csv"))
        assert len(csv_files) == 1
        content = csv_files[0].read_text()
        assert "TestModel" in content
        assert "fake" in content
