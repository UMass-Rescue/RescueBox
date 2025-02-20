import os
from pathlib import Path
#from fastapi.testclient import TestClient
from rb.api.models import Input, BatchFileInput
from rb_audio_transcription.main import app
#from rb.api.main import app as fapp
from typer.testing import CliRunner


runner = CliRunner()
#client = TestClient(fapp, base_url='http://localhost:8000', raise_server_exceptions=True)


# these 4 cli calls works #
def test_routes_command():
    result = runner.invoke(app, ["api/routes"])
    print(result.stdout)
    print(result)
    assert result.stdout is ''
    assert result.exit_code == 0


def test_metadata_command():
    result = runner.invoke(app, ["/api/app_metadata"])
    print(result.stdout)
    print(result)
    assert result.stdout is ''
    assert result.exit_code == 0

def test_schema_command():
    result = runner.invoke(app, ["/audio/task_schema"])
    print(result.stdout)
    print(result)
    assert result.stdout is ''
    assert result.exit_code == 0


def test_transcribe_command():
    cwd = Path.cwd()
    full_path = os.path.join(cwd, 'src','rb-audio-transcription','tests', 'sample.mp3')
    result = runner.invoke(app, ["audio/transcribe", full_path, "'e1': 'example', 'e2' : 0.1, 'e3': 1"])
    print(result.stdout)
    print(result)
    assert result.stdout is ''
    assert result.exit_code == 0

# pytest -vvvv works upto here
'''
def test_read_metadata():
    client.base_url = 'http://localhost:8000'
    response = client.get("/api/routes")
    print(response.json())
    assert response is None
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}


inputs = {
    "file_inputs": Input(
        root=BatchFileInput.model_validate(
            {"files": [{"path": "C:\\work\\audio\\samples\\sample.mp3"}]}
        )
    )
}
example_parameters = {
    "example_parameter": "Some string",
    "example_parameter2": 0.25,
    "example_parameter3": 3,
}
'''