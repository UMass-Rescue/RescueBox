import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from rb.api.models import FileResponse, FileType, ResponseBody

from frontend.chatbot.pipeline_context import get_pipeline_output_path
from frontend.database.job_db import init_database
from frontend.pages.chatbot.chat_page import ChatbotPage
from frontend.pages.chatbot.routes import handle_rerun_parameter


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pipeline_output_path_resolves_from_real_job_db(tmp_path):
    db = await init_database(tmp_path / "jobs.db")
    job = await db.create_job(
        request_body={"inputs": {}, "parameters": {}},
        task_schema={},
        endpoint="image_summary/summarize-images",
    )
    response = ResponseBody(
        FileResponse(
            filename="o.txt",
            content="x",
            file_type=FileType.TEXT,
            path=str(tmp_path / "result" / "o.txt"),
            title="out",
        )
    )
    await db.update_job_status(job.uid, "Completed", response_body=response)

    output_path = get_pipeline_output_path(job.uid)
    assert output_path is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_handle_rerun_parameter_delegates_to_chatbot_page():
    fake_chatbot = MagicMock(spec=ChatbotPage)
    handle_rerun_tool = AsyncMock()
    fake_chatbot.handle_rerun_tool = handle_rerun_tool

    with patch(
        "frontend.pages.chatbot.routes.ChatbotPage.get_instance",
        return_value=fake_chatbot,
    ):
        await handle_rerun_parameter("msg-1")

    handle_rerun_tool.assert_awaited_once_with("msg-1")
