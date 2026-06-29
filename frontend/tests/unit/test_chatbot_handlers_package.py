"""Tests for pages.chatbot.handlers package surface (post-split)."""

from frontend.pages import chatbot as chatbot_pkg
from frontend.pages.chatbot import handlers


def test_handlers_exports_job_orchestration_only():
    assert "JobSubmissionOrchestrator" in handlers.__all__
    assert "PipelineHandler" in handlers.__all__
    assert "load_and_show_form" not in handlers.__all__
    assert "show_results" not in handlers.__all__


def test_chatbot_public_exports_ui_flow_separately():
    assert hasattr(chatbot_pkg, "load_and_show_form")
    assert hasattr(chatbot_pkg, "show_results")
    assert hasattr(chatbot_pkg, "JobSubmissionOrchestrator")


def test_chatbot_public_exports_do_not_include_db_singletons():
    assert not hasattr(chatbot_pkg, "get_job_db")
    assert not hasattr(chatbot_pkg, "get_chat_history_db")
