from age_gender_classifier.server.server_onnx import app, APP_NAME, create_transform_case_task_schema
from rb.lib.common_tests import RBAppTest
from rb.api.models import AppMetadata
from pathlib import Path
from unittest.mock import patch
import json

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




# TODO
# Test end point
# Fsster API endpoit: self.client.post(summarize_api, json=input_json)
# typer command : result = self.runner.invoke(
        #     self.cli_app, [summarize_api, input_str, parameter_str]
        # )