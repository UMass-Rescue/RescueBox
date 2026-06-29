from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from rb.api.models import FileResponse, FileType, InputType, ResponseBody

from frontend.chatbot.pipeline_context import (
    find_input_directory_key,
    get_pipeline_output_path,
    inject_pipeline_path,
)


def _schema_with_keys(*keys: str):
    inputs = [SimpleNamespace(key=k, input_type=InputType.DIRECTORY) for k in keys]
    return SimpleNamespace(inputs=inputs)


def test_find_input_directory_key_prefers_input_named_field():
    schema = _schema_with_keys("output_dir", "input_dir")
    assert find_input_directory_key(schema) == "input_dir"


def test_find_input_directory_key_falls_back_to_first_directory():
    schema = _schema_with_keys("images", "results")
    assert find_input_directory_key(schema) == "images"


def test_get_pipeline_output_path_returns_none_when_job_missing():
    with patch("frontend.chatbot.pipeline_context.get_job_db") as mock_get_db:
        mock_get_db.return_value.get_job_by_uid_sync.return_value = None
        assert get_pipeline_output_path("JOB_X") is None


def test_get_pipeline_output_path_uses_response_extractor():
    file_response = FileResponse(
        filename="x.txt",
        content="x",
        file_type=FileType.TEXT,
        path="/tmp/out/x.txt",
        title="x",
    )
    response = ResponseBody(file_response)
    mock_job = MagicMock()
    mock_job.response = response
    with patch("frontend.chatbot.pipeline_context.get_job_db") as mock_get_db, patch(
        "frontend.chatbot.pipeline_context.extract_output_path", return_value="/tmp/out"
    ) as mock_extract:
        mock_get_db.return_value.get_job_by_uid_sync.return_value = mock_job
        assert get_pipeline_output_path("JOB_1") == "/tmp/out"
        mock_extract.assert_called_once_with(response)


def test_inject_pipeline_path_injects_resolved_output():
    schema = _schema_with_keys("input_dir", "output_dir")
    with patch(
        "frontend.chatbot.pipeline_context.get_pipeline_output_path",
        return_value="/tmp/chained",
    ):
        out = inject_pipeline_path({"x": 1}, schema, "JOB_1")
    assert out["x"] == 1
    assert out["input_dir"] == "/tmp/chained"


def test_inject_pipeline_path_no_output_keeps_arguments():
    schema = _schema_with_keys("input_dir")
    with patch(
        "frontend.chatbot.pipeline_context.get_pipeline_output_path", return_value=None
    ):
        out = inject_pipeline_path({"x": 1}, schema, "JOB_1")
    assert out == {"x": 1}
