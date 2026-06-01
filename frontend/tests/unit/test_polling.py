from unittest.mock import MagicMock
from frontend.pages.chatbot import ChatbotPage
from frontend.chatbot.config import ChatbotConfig
import pytest

@pytest.mark.asyncio
async def test_polling_triggers_show_results(monkeypatch):
    """Ensure polling detects job completion and triggers result rendering."""
    # Prepare ChatbotPage
    page = ChatbotPage(ChatbotConfig())
    page.chat_container = MagicMock()
    page.chat_container.client = True
    # patch get_job_db used inside _poll_job_status
    class FakeJobDB:
        def __init__(self):
            self.calls = 0

        async def get_job_by_uid(self, uid):
            self.calls += 1
            if self.calls < 2:
                class J:
                    status = 'Running'
                    response = None
                return J()
            else:
                class J:
                    status = 'Completed'
                    response = {'root': {'output_type': 'text', 'value': 'done'}}
                return J()

    monkeypatch.setattr('frontend.pages.chatbot.get_job_db', lambda: FakeJobDB())

    # patch show_results to AsyncMock
    called = {"called": False}

    async def fake_show_results(container, response_body, job_id):
        called["called"] = True

    monkeypatch.setattr('frontend.pages.chatbot.show_results', fake_show_results)

    # Run poll (should exit after job completes)
    await page._poll_job_status("JOB_X", "endpoint", interval=0.01)
    assert called["called"] is True
