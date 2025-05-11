from age_gender_classifier.server.server_onnx import app, APP_NAME, create_transform_case_task_schema
from rb.lib.common_tests import RBAppTest
from rb.api.models import AppMetadata, ResponseBody, TextResponse
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




    # @patch(
    #     "age_gender_classifier.server.server_onnx.age_classifier",
    #     return_value=ResponseBody(
    #         TextResponse(
    #             value=json.dumps({"result": "success"}),
    #             title="Mocked Result"
    #         )
    #     )
    # )
    @patch("age_gender_classifier.onnx_models.survey_models.SurveyModels.main_predict")
    def test_api_age_classifier(self, age_class_mock):
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

        assert response.status_code == 200
        body = response.json()

        input_files = [
            f for f in full_path.glob("*") if f.suffix in [".jpg", ".png"]
        ]

        results = json.loads(body["value"])
        assert results is not None
        
        # print("Results:", results.keys())
        # print("Results:", results)
        # print("Input Files:", input_files)
        # assert len(results) == len(input_files)
#         assert set(expected_files) == set(results)
#         for file in results:
#             assert file.endswith(".txt")
#             assert Path(file).read_text() == "Mocked summary"



    # TODO typer command : result = self.runner.invoke(self.cli_app, [summarize_api, input_str, parameter_str])
    # @patch("text_summary.summarize.ensure_model_exists")
    # @patch("text_summary.summarize.summarize", return_value="Mocked summary")
#     def test_age_class_command(self, summarize_mock, ensure_model_exists_mock):
# #         summarize_api = f"/{APP_NAME}/summarize"
# #         full_path = Path.cwd() / "src" / "text-summary" / "test_input"
# #         output_path = Path.cwd() / "src" / "text-summary" / "test_output"
# #         input_str = f"{str(full_path)},{str(output_path)}"
# #         parameter_str = "gemma3:1b"
# #         result = self.runner.invoke(
# #             self.cli_app, [summarize_api, input_str, parameter_str]
# #         )
# #         assert result.exit_code == 0, f"Error: {result.output}"
# #         output_files = list(output_path.glob("*.txt"))
# #         assert len(output_files) == 3
# #         for file in output_files:
# #             with open(file, "r") as f:
# #                 content = f.read()
# #                 assert "Mocked summary" == content
#         pass

#     # @patch("text_summary.summarize.summarize", return_value="Mocked summary")
#     def test_bad_path(self, summarize_mock, ensure_model_exists_mock):
#         summarize_api = f"/{APP_NAME}/summarize"
#         bad_path = Path.cwd() / "src" / "text-summary" / "bad_tests"
#         input_str = f"{str(bad_path)},{str(bad_path)}"
#         parameter_str = "gemma3:1b"
#         result = self.runner.invoke(
#             self.cli_app, [summarize_api, input_str, parameter_str]
#         )
#         assert result.exit_code != 0
    #    pass