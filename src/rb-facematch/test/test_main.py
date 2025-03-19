"""test facematch typer cli commands and fastapi api calls"""

from pathlib import Path
from pydantic import DirectoryPath, FilePath
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from typer.testing import CliRunner

# this app is for cli testing using typer CliRunner
from rb_facematch.main import app as cli_app
from rb_facematch.main import BulkUploadInputs, FindFaceInputs
from rb.api.models import (
    API_APPMETDATA,
    API_ROUTES,
    PLUGIN_SCHEMA_SUFFIX,
    BatchDirectoryInput,
    BatchFileInput,
    FileInput,
    DirectoryInput,
    ResponseBody,
)

# this app is for fastapi testing using TestClient
from rb.api.main import app as api_app


runner = CliRunner()
client = TestClient(api_app)

r"""
 run testss from test folder
 cd C:\xxxx\RescueBox && poetry run pytest  src\rb-facematch\test\test_main.py -vvv
 
 --log-cli-level=10 fails with ValueError: I/O operation on closed file. logging issue ??
"""


def test_routes_command():
    """call typer cli to get routes"""
    result = runner.invoke(cli_app, [API_ROUTES])
    assert result != ""
    assert result.exit_code == 0


def test_metadata_command():
    result = runner.invoke(cli_app, [API_APPMETDATA])
    assert result != ""
    assert result.exit_code == 0


def test_schema_command():
    result = runner.invoke(cli_app, [f"upload{PLUGIN_SCHEMA_SUFFIX}"])
    assert result != ""
    print(result)
    print(result.stdout)
    assert result.exit_code == 0


def test_schema_find_command():
    result = runner.invoke(cli_app, [f"find_face_task{PLUGIN_SCHEMA_SUFFIX}"])
    assert result != ""
    print(result)
    print(result.stdout)
    assert result.exit_code == 0


def test_negative_test():
    """facematch bulkupload command cli to bulkupload with invalid facematch file"""  # type: ignore
    bad_full_path = Path.cwd().joinpath("src", "rb-facematch", "bad_tests")
    result = runner.invoke(
        cli_app,
        [
            "bulkupload",
            jsonable_encoder(bad_full_path),
            "'dropdown_database_name': 'Create a new database', 'database_name' : 'xx'",
        ],
    )
    print("negative test ", result.stdout)
    assert "Aborted." in result.stdout
    assert result.exit_code == 1


def test_cli_upload_command():
    r"""call facematch bulkupload command typer cli to bulkupload a sample facematch file"""
    full_path = Path.cwd() / "src" / "rb-facematch" / "test"
    print("cli test", full_path)
    result = runner.invoke(
        cli_app,
        [
            "bulkupload",
            jsonable_encoder(full_path),
            "'dropdown_database_name': \"sample_database\", 'database_name' : \"xx\"",
        ],
    )
    print(result)
    assert result.stdout is not None
    assert result.exit_code == 0


def test_api_upload_command():
    r"""call facematch bulkupload command fastapi to bulkupload a sample facematch file"""

    full_path = Path.cwd() / "src" / "rb-facematch" / "test"

    dir_input = DirectoryInput(path=DirectoryPath(full_path))
    print(dir_input)
    # force validation of DirectoryInput full_path
    BulkUploadInputs(directory_paths=BatchDirectoryInput(directories=[dir_input]))

    # BulkUploadParameters
    bulk = {
        "inputs": {"directory_paths": {"directories": jsonable_encoder([dir_input])}},
        "parameters": {
            "dropdown_database_name": "sample_database",
            "database_name": "sample_database",
        },
    }

    response = client.post("/facematch/bulkupload", json=bulk)

    assert response is not None
    assert response.status_code == 200
    output = ResponseBody(**response.json())
    assert output is not None
    print(output.root)
    txt = [txt for txt in output.root]
    assert txt is not None
    assert len(txt) > 0


def test_client_routes():
    """call fastapi /api/routes"""
    response = client.get("/facematch/routes")
    assert response is not None
    assert response.status_code == 200
    assert response.json() is not None


def test_client_metadata():
    """call fastapi /api/routes"""
    response = client.get("/facematch/app_metadata")
    assert response is not None
    assert response.status_code == 200
    assert response.json() is not None


def test_cli_find_face_command():
    r"""call facematch find_face command typer cli to find_face a sample file"""
    full_path = Path.cwd() / "src" / "rb-facematch" / "test" / "test_image.jpg"
    print("cli test", full_path)
    result = runner.invoke(
        cli_app,
        [
            "findface",
            jsonable_encoder(full_path),
            "'database_name': \"sample_database\", 'similarity_threshold' : 0.7",
        ],
    )
    print(result)
    assert result.stdout is not None
    assert result.exit_code == 0


def test_api_find_face_command():
    r"""call facematch bulkupload command fastapi to bulkupload a sample file"""

    full_path = Path.cwd() / "src" / "rb-facematch" / "test" / "test_image.jpg"

    file_input = FileInput(path=FilePath(full_path))
    print(file_input)
    # force validation of DirectoryInput full_path
    FindFaceInputs(image_paths=BatchFileInput(files=[file_input]))

    # BulkUploadParameters
    bulk = {
        "inputs": {"image_paths": {"files": jsonable_encoder([file_input])}},
        "parameters": {
            "database_name": "sample_database",
            "similarity_threshold": "0.7",
        },
    }
    response = client.post("/facematch/findface", json=bulk)

    assert response is not None
    assert response.status_code == 200
    output = ResponseBody(**response.json())
    assert output is not None
    print(output.root)
    txt = [txt for txt in output.root]
    assert txt is not None
    assert len(txt) > 0
