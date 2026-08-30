import json
import logging
from pathlib import Path

import pytest
from age_and_gender_detection.main import APP_NAME, server, task_schema
from age_and_gender_detection.main import app as cli_app
from age_and_gender_detection.model import AgeGenderDetector
from rb.api.models import ResponseBody
from rb.lib.common_tests import RBAppTest


class DebugOnlyFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.DEBUG


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

TEST_IMAGES_DIR = Path("src/age_and_gender_detection/test_images")

EXPECTED_OUTPUT = {
    str(TEST_IMAGES_DIR / "gela.jpg"): [
        {"box": [2287, 715, 3514, 1943], "gender": "Female", "age": "(25-32)"}
    ],
    str(TEST_IMAGES_DIR / "guy.jpg"): [
        {"box": [812, 1409, 1620, 2218], "gender": "Male", "age": "(25-32)"}
    ],
    str(TEST_IMAGES_DIR / "baby.jpg"): [
        {"box": [345, 217, 592, 464], "gender": "Female", "age": "(0-2)"}
    ],
    str(TEST_IMAGES_DIR / "kid1.jpg"): [
        {"box": [229, 58, 551, 381], "gender": "Male", "age": "(4-6)"}
    ],
}


class TestAgeGender(RBAppTest):
    def setup_method(self):
        self.set_app(cli_app, APP_NAME)
        models_dir = Path(
            "src/age_and_gender_detection/age_and_gender_detection/onnx_models"
        )
        # If model files are not present in the workspace, skip these heavier integration tests.
        if not (models_dir / "version-RFB-640.onnx").exists():
            pytest.skip("Age/Gender ONNX models not available in CI environment")
        self.model = AgeGenderDetector(
            face_detector_path=models_dir / "version-RFB-640.onnx",
            age_classifier_path=models_dir / "age_googlenet.onnx",
            gender_classifier_path=models_dir / "gender_googlenet.onnx",
        )

    def get_metadata(self):
        assert server._app_metadata is not None
        return server._app_metadata

    def get_all_ml_services(self):
        return [
            (0, "predict", "Age and Gender", task_schema()),
        ]

    def test_predict_age_gender(self):
        input_path = Path("src/age_and_gender_detection/test_images")
        res = self.model.predict_age_and_gender_on_dir(input_path)
        assert res is not None
        assert len(res) == 4
        for k, v in EXPECTED_OUTPUT.items():
            assert k in res
            assert len(res[k]) == len(v)
            v = v[0]
            assert v.keys() == res[k][0].keys()
            assert v["gender"] == res[k][0]["gender"]
            assert v["age"] == res[k][0]["age"]
            # not testing the box because the results may vary slightly

    def test_age_gender_command(self, caplog):
        with caplog.at_level("INFO"):
            age_gender_api = f"/{APP_NAME}/predict"
            input_path = Path("src/age_and_gender_detection/test_images")
            result = self.runner.invoke(self.cli_app, [age_gender_api, str(input_path)])
            assert result.exit_code == 0, f"Error: {result.output}"
            expected_files = [
                str(Path(s))
                for s in [
                    "src/age_and_gender_detection/test_images/gela.jpg",
                    "src/age_and_gender_detection/test_images/guy.jpg",
                    "src/age_and_gender_detection/test_images/baby.jpg",
                    "src/age_and_gender_detection/test_images/kid1.jpg",
                ]
            ]
            # The implementation logs the response as a BatchFileResponse; check captured text for file paths.
            captured_text = (
                caplog.text if hasattr(caplog, "text") else " ".join(caplog.messages)
            )
            for expected_file in expected_files:
                # Match on filename only to avoid platform-specific path-escaping differences
                assert Path(expected_file).name in captured_text

    def test_invalid_path(self):
        age_gender_api = f"/{APP_NAME}/predict"
        invalid_path = Path("src/age_and_gender_detection/bad_path")
        result = self.runner.invoke(self.cli_app, [age_gender_api, str(invalid_path)])
        assert result.exit_code != 0, f"Error: {result.output}"

    def test_age_gender_api(self):
        age_gender_api = f"/{APP_NAME}/predict"
        input_path = Path("src/age_and_gender_detection/test_images")
        input = {
            "inputs": {
                "image_directory": {
                    "path": str(input_path),
                }
            }
        }
        response = self.client.post(age_gender_api, json=input)
        assert response.status_code == 200
        body = ResponseBody(**response.json())
        assert body.root is not None
        # Support both BatchFileResponse and TextResponse outputs.
        if getattr(body.root, "output_type", "") == "batchfile":
            files = getattr(body.root, "files", [])
            assert len(files) == 4
            # Build a mapping from path -> metadata for assertions
            file_map = {f.path: f.metadata for f in files}
            for k, v in EXPECTED_OUTPUT.items():
                assert k in file_map
                expected_meta = v[0]
                # Compare gender/age from metadata
                assert file_map[k]["Gender"] == expected_meta["gender"]
                assert file_map[k]["Age"] == expected_meta["age"]
        else:
            # Fallback: older behavior where root.value contained JSON string
            preds = json.loads(body.root.value)
            assert len(preds) == 4
            for k, v in EXPECTED_OUTPUT.items():
                assert k in preds
                assert len(preds[k]) == len(v)
                v = v[0]
                assert v.keys() == preds[k][0].keys()
                assert v["gender"] == preds[k][0]["gender"]
                assert v["age"] == preds[k][0]["age"]
