''' test audio typer cli commands and fastapi api calls'''
import os
import logging
from pathlib import Path
from fastapi.testclient import TestClient
from typer.testing import CliRunner
# this app is for cli testing using typer CliRunner
from rb_audio_transcription.main import app as cli_app
from rb.api.models import API_APPMETDATA, API_ROUTES, PLUGIN_SCHEMA_SUFFIX
# this app is for fastapi testing using TestClient
from rb.api.main import app as api_app
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

runner = CliRunner()
client = TestClient(api_app)

r'''
 run testss from test folder
 cd C:\xxxx\RescueBox\src\rb-audio-transcription\tests
 pytest --log-cli-level=10 audio_test.py
 or 
 cd C:\xxxx\RescueBox && poetry run pytest --log-cli-level=10 src\rb-audio-transcription\tests\audio_test.py  -s
'''


def test_routes_command():
    ''' call typer cli to get routes'''
    result = runner.invoke(cli_app, [API_ROUTES])
    logger.info(f'Test completed successfully {result.exit_code}')
    assert result is not ""
    assert result.exit_code == 0


def test_metadata_command():
    result = runner.invoke(cli_app, [API_APPMETDATA])
    assert result is not ""
    assert result.exit_code == 0


def test_schema_command():
    result = runner.invoke(cli_app, [f"task{PLUGIN_SCHEMA_SUFFIX}"])
    assert result is not ""
    assert result.exit_code == 0

def test_negative_test():
    ''' call audio transcribe command cli to transcribe with invalid audio file'''
    cwd = Path.cwd()
    full_path = os.path.join(
        cwd, "src", "rb-audio-transcription", "tests", "does_not_exist.mp3"
    )
    result = runner.invoke(
        cli_app, ['transcribe', full_path, "'e1': 'example', 'e2' : 0.1, 'e3': 1"]
    )
    logger.info(f'Test expected to fail:{result.output}')
    assert "Aborted." in result.stdout
    assert result.exit_code == 1

def test_transcribe_command():
    ''' call audio transcribe command cli to transcribe a sample audio file'''
    cwd = Path.cwd()
    full_path = os.path.join(
        cwd, "src", "rb-audio-transcription", "tests", "sample.mp3"
    )
    result = runner.invoke(
        cli_app, ['transcribe', full_path, "'e1': 'example', 'e2' : 0.1, 'e3': 1"]
    )
    assert result.stdout is ""
    assert result.exit_code == 0

def test_client_routes():
    ''' call fastapi /api/routes '''
    response = client.get('/api/routes')
    assert response is not None
    assert response.status_code == 200
    assert response.json() is not None



def test_client_metadata():
    ''' call fastapi /api/routes '''
    response = client.get('/api/app_metadata')
    assert response is not None
    assert response.status_code == 200
    assert response.json() is not None


# TODO: other api routes tests example : client.post(f'/manage/info')
