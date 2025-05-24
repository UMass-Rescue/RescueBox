from ufdr_mounter.ufdr_server import app as cli_app, APP_NAME, ufdr_task_schema, server
from rb.lib.common_tests import RBAppTest
from rb.api.models import AppMetadata, ResponseBody
from pathlib import Path
import os

# Note : pre req libfuse library must be available in the test environment


class TestUFDRMounter(RBAppTest):
    def setup_method(self):
        self.set_app(cli_app, APP_NAME)

    def get_metadata(self):
        """Return app metadata for testing"""
        return server._app_metadata

    def get_all_ml_services(self):
        return [
            (0, "mount", "Mount UFDR", ufdr_task_schema()),
        ]

    def test_invalid_path(self):
        mount_api = f"/{APP_NAME}/mount"
        input_str = "not/a/real/file.ufdr,bad_mount_point"
        result = self.runner.invoke(self.cli_app, [mount_api, input_str, ""])
        assert (
            result.exit_code != 0
        ), f"Expected failure for bad path, got: {result.output}"

    def test_mount_command(self, caplog):
        mount_api = f"/{APP_NAME}/mount"
        test_file = Path("src/ufdr_mounter/ufdr_mounter/testdata/test.ufdr").resolve()
        mount_dir = Path("mnt/test_mount").resolve()

        # ensure directory exists
        os.makedirs(mount_dir, exist_ok=True)
        input_str = f"{test_file},{mount_dir}"
        result = self.runner.invoke(self.cli_app, [mount_api, input_str, ""])
        print("debug", result)

    def test_mount_api(self):
        mount_api = f"/{APP_NAME}/mount"
        test_file = Path("src/ufdr_mounter/ufdr_mounter/testdata/test.ufdr").resolve()
        mount_dir = Path("mnt/test_mount").resolve()

        input_json = {
            "inputs": {
                "ufdr_file": {"path": str(test_file)},
                "mount_name": {"text": str(mount_dir)},
            },
            "parameters": {},
        }
        response = self.client.post(mount_api, json=input_json)
        print("debug", response)
