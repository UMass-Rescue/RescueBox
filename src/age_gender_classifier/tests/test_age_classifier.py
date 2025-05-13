from age_gender_classifier.server.server_onnx import app, APP_NAME, create_transform_case_task_schema
from rb.lib.common_tests import RBAppTest
from rb.api.models import AppMetadata
from pathlib import Path
from unittest.mock import patch
import json
import pandas as pd

class TestAgeClassifier(RBAppTest):
    def setup_method(self):
        self.set_app(app, APP_NAME)

    def get_metadata(self):
        return AppMetadata(
            name=APP_NAME,
            author="UMass Rescue",
            version="0.1.0",
            info="Model to classify ages from images.",
            plugin_name=APP_NAME,
        )

    def get_all_ml_services(self):
        return [
            (0, "age_classifier", "Age and Gender Classifier", create_transform_case_task_schema()),
        ]

    @patch("age_gender_classifier.onnx_models.survey_models.SurveyModels.__init__", return_value=None)
    @patch("age_gender_classifier.onnx_models.survey_models.SurveyModels.main_predict")
    def test_api_age_classifier(self, age_class_mock, init_mock):
        age_class_mock.return_value = pd.DataFrame()

        age_class_api = f"/{APP_NAME}/age_classifier"
        full_path = Path.cwd() / "src" / "age_gender_classifier" / "age_gender_classifier" / "onnx_models" / "test_images"
        input_json = {
            "inputs": {
                "input_dataset": {"path": str(full_path)},
            },
            "parameters": {"age_threshold": 20},
        }
        response = self.client.post(age_class_api, json=input_json)
        body = response.json()

        input_files = [
            f for f in full_path.glob("*") if f.suffix in [".jpg", ".png"]
        ]
        results = json.loads(body["value"])

        assert response.status_code == 200
        assert results is not None
        assert isinstance(results, dict)

    @patch("age_gender_classifier.onnx_models.survey_models.SurveyModels.__init__", return_value=None)
    @patch("age_gender_classifier.onnx_models.survey_models.SurveyModels.main_predict")
    def test_age_class_command(self, age_class_mock, init_mock):
        age_class_mock.return_value = pd.DataFrame()
        age_class_api = f"/{APP_NAME}/age_classifier"
        full_path = Path.cwd() / "src" / "age_gender_classifier" / "age_gender_classifier" / "onnx_models" / "test_images"
        parameter_str = "20"
        result = self.runner.invoke(
            self.cli_app, [age_class_api, str(full_path), parameter_str]
        )
        assert result.exit_code == 0, f"Error: {result.output}"

    @patch("age_gender_classifier.onnx_models.survey_models.SurveyModels.__init__", return_value=None)
    @patch("age_gender_classifier.onnx_models.survey_models.SurveyModels.main_predict")
    def test_bad_path(self, age_class_mock, init_mock):
        age_class_mock.return_value = pd.DataFrame()
        age_class_api = f"/{APP_NAME}/age_classifier"
        full_path = Path.cwd() / "src" / "age_gender_classifier" / "age_gender_classifier" / "onnx_models" / "no_dir"
        parameter_str = "20"
        result = self.runner.invoke(
            self.cli_app, [age_class_api, str(full_path), parameter_str]
        )
        assert result.exit_code != 0
