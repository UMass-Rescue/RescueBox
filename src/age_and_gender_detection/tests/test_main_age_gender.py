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
            version="2.1.0",
            info="Model to classify the age and gender of all faces in an image.",
            plugin_name=APP_NAME,
            gpu=True,
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
                Path(s)
                for s in [
                    "src/age_and_gender_detection/test_images/gela.jpg",
                    "src/age_and_gender_detection/test_images/guy.jpg",
                    "src/age_and_gender_detection/test_images/baby.jpg",
                    "src/age_and_gender_detection/test_images/kid1.jpg",
                ]
            ]
            # Combine all log messages into one string for easier searching
            all_messages = " ".join(caplog.messages)
            
            for expected_file in expected_files:
                # Create multiple path representations to check for cross-platform compatibility
                posix_path = expected_file.as_posix()  # Forward slashes: src/age_and_gender_detection/test_images/gela.jpg
                native_path = str(expected_file)  # OS-native: src\age_and_gender_detection\test_images\gela.jpg on Windows
                escaped_path = native_path.replace("\\", "\\\\")  # Double-escaped: src\\\\age_and_gender_detection\\\\test_images\\\\gela.jpg
                
                # Check if any path representation appears in the log messages
                assert any(path_repr in all_messages for path_repr in [posix_path, native_path, escaped_path]), \
                    f"Expected file {expected_file} not found in log messages. Checked: {posix_path}, {native_path}, {escaped_path}"

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
        assert hasattr(body.root, 'files'), "Expected BatchFileResponse with files attribute"
        
        # Convert BatchFileResponse to the old dict format for comparison
        files = body.root.files
        assert len(files) == 4, f"Expected 4 files, got {len(files)}"
        
        # Check that all expected images are present in the response
        returned_paths = {file_resp.path for file_resp in files}
        expected_paths = set(EXPECTED_OUTPUT.keys())
        assert returned_paths == expected_paths, \
            f"Mismatch in returned paths. Expected: {expected_paths}, Got: {returned_paths}"
        
        # Verify each file's predictions match expectations
        for file_resp in files:
            image_path = file_resp.path
            expected = EXPECTED_OUTPUT[image_path][0]
            assert file_resp.metadata["Gender"] == expected["gender"]
            assert file_resp.metadata["Age"] == expected["age"]
