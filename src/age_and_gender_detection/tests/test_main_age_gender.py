from age_and_gender_detection.main import app as cli_app, APP_NAME, task_schema
from age_and_gender_detection.model import AgeGenderDetector
from rb.lib.common_tests import RBAppTest
from rb.api.models import AppMetadata
from pathlib import Path
from rb.api.models import ResponseBody
import logging
import json


class DebugOnlyFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.DEBUG


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

EXPECTED_OUTPUT = {
    "src/age_and_gender_detection/test_images/bella.jpg": [
        {"box": [246, 257, 847, 858], "gender": "Female", "age": "(25-32)"}
    ],
    "src/age_and_gender_detection/test_images/bruce.jpg": [
        {"box": [51, 122, 328, 399], "gender": "Male", "age": "(25-32)"}
    ],
    "src/age_and_gender_detection/test_images/baby.jpg": [
        {"box": [345, 217, 592, 464], "gender": "Female", "age": "(0-2)"}
    ],
    "src/age_and_gender_detection/test_images/kid.jpg": [
        {"box": [476, 143, 696, 364], "gender": "Male", "age": "(4-6)"}
    ],
}


class TestAgeGender(RBAppTest):
    def setup_method(self):
        self.set_app(cli_app, APP_NAME)
        models_dir = Path("src/age_and_gender_detection/models")
        self.model = AgeGenderDetector(
            face_detector_path=models_dir / "version-RFB-640.onnx",
            age_classifier_path=models_dir / "age_googlenet.onnx",
            gender_classifier_path=models_dir / "gender_googlenet.onnx",
        )

    def get_metadata(self):
        return AppMetadata(
            name="Age and Gender Classifier",
            author="UMass Rescue",
            version="0.1.0",
            info="Model to classify the age and gender of all faces in an image.",
            plugin_name=APP_NAME,
        )

    def get_all_ml_services(self):
        return [
            (0, "predict", "Age and Gender Classifier", task_schema()),
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
                "src/age_and_gender_detection/test_images/bella.jpg",
                "src/age_and_gender_detection/test_images/bruce.jpg",
                "src/age_and_gender_detection/test_images/baby.jpg",
                "src/age_and_gender_detection/test_images/kid.jpg",
            ]
            for expected_file in expected_files:
                assert any(expected_file in message for message in caplog.messages)

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
        print(f"Response body: {body}")
        assert body.root is not None
        preds = json.loads(body.root.value)
        assert len(preds) == 4
        for k, v in EXPECTED_OUTPUT.items():
            assert k in preds
            assert len(preds[k]) == len(v)
            v = v[0]
            assert v.keys() == preds[k][0].keys()
            assert v["gender"] == preds[k][0]["gender"]
            assert v["age"] == preds[k][0]["age"]
