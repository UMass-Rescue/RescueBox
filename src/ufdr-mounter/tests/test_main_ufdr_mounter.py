import os
import uuid
from pathlib import Path

import pytest
from rb.lib.common_tests import RBAppTest

from ufdr_mounter.ufdr_server import (
    APP_NAME,
    server,
    ufdr_task_schema,
    validate_mount_folder,
    validate_mount_name_tmp,
)
from ufdr_mounter.ufdr_server import (
    app as cli_app,
)

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

    def test_mount_command(self, caplog, tmp_path):
        mount_api = f"/{APP_NAME}/mount"
        test_file = Path("src/ufdr-mounter/ufdr_mounter/testdata/test.ufdr").resolve()
        mount_dir = f"/tmp/rb_ufdr_cmd_{uuid.uuid4().hex[:10]}"

        input_str = f"{test_file},{mount_dir}"
        result = self.runner.invoke(self.cli_app, [mount_api, input_str, ""])
        print("debug", result)

    def test_mount_api(self, tmp_path):
        mount_api = f"/{APP_NAME}/mount"
        test_file = Path("src/ufdr-mounter/ufdr_mounter/testdata/test.ufdr").resolve()
        mount_dir = f"/tmp/rb_ufdr_api_{uuid.uuid4().hex[:10]}"

        input_json = {
            "inputs": {
                "ufdr_file": {"path": str(test_file)},
                "mount_name": {"text": str(mount_dir)},
            },
            "parameters": {},
        }
        response = self.client.post(mount_api, json=input_json)
        print("debug", response)

    def test_mount_api_rejects_non_tmp_mount_name(self):
        mount_api = f"/{APP_NAME}/mount"
        test_file = Path("src/ufdr-mounter/ufdr_mounter/testdata/test.ufdr").resolve()
        input_json = {
            "inputs": {
                "ufdr_file": {"path": str(test_file)},
                "mount_name": {"text": "/mnt/case1"},
            },
            "parameters": {},
        }
        response = self.client.post(mount_api, json=input_json)
        assert response.status_code == 400
        assert "tmp" in response.json().get("detail", "").lower()

    @pytest.mark.skipif(
        os.name == "nt",
        reason="POSIX: / is always a mount point",
    )
    def test_mount_api_validation_returns_400(self):
        """Invalid mount folder must be HTTP 400, not 200 with an error body."""
        mount_api = f"/{APP_NAME}/mount"
        test_file = Path("src/ufdr-mounter/ufdr_mounter/testdata/test.ufdr").resolve()
        input_json = {
            "inputs": {
                "ufdr_file": {"path": str(test_file)},
                "mount_name": {"text": "/"},
            },
            "parameters": {},
        }
        response = self.client.post(mount_api, json=input_json)
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert isinstance(detail, str)
        # "/" normalizes to empty mount path; may also fail /tmp layout first for other inputs.
        assert "mount" in detail.lower()


class TestValidateMountNameTmp:
    def test_accepts_tmp_single_segment(self):
        ok, msg = validate_mount_name_tmp("/tmp/case123")
        assert ok is True
        assert msg == ""

    def test_rejects_nested_under_tmp(self):
        ok, msg = validate_mount_name_tmp("/tmp/a/b")
        assert ok is False
        assert "tmp" in msg.lower()

    def test_rejects_mnt(self):
        ok, msg = validate_mount_name_tmp("/mnt/case1")
        assert ok is False

    def test_rejects_relative(self):
        ok, msg = validate_mount_name_tmp("myfolder")
        assert ok is False


class TestValidateMountFolder:
    def test_empty_path(self):
        ok, msg = validate_mount_folder("")
        assert ok is False
        assert "empty" in msg.lower()

    def test_empty_dir_ok(self, tmp_path):
        d = tmp_path / "empty_mount"
        d.mkdir()
        ok, msg = validate_mount_folder(str(d))
        assert ok is True
        assert msg == ""

    def test_nonempty_dir_rejected(self, tmp_path):
        d = tmp_path / "has_files"
        d.mkdir()
        (d / "x.txt").write_text("x")
        ok, msg = validate_mount_folder(str(d))
        assert ok is False
        assert "empty" in msg.lower()

    def test_creatable_under_tmp_ok(self, tmp_path):
        new_dir = tmp_path / "new" / "nested" / "mount"
        ok, msg = validate_mount_folder(str(new_dir))
        assert ok is True
        assert msg == ""

    @pytest.mark.skipif(
        os.name == "nt",
        reason="POSIX mount-point checks",
    )
    def test_root_is_mount_rejected(self):
        ok, msg = validate_mount_folder("/")
        assert ok is False
        assert "mount point" in msg.lower()
