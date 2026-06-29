"""Unit tests for chatbot storage read helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from frontend.pages.chatbot.storage_reads import read_pipeline_job_id


@pytest.fixture
def patched_app(monkeypatch):
    mock_app = MagicMock()
    mock_app.storage.user = MagicMock()
    mock_app.storage.user.get = MagicMock(return_value="job-42")
    monkeypatch.setattr("frontend.utils.storage.app", mock_app)
    return mock_app


def test_read_pipeline_job_id_returns_value(patched_app):
    assert read_pipeline_job_id() == "job-42"


def test_read_pipeline_job_id_returns_none_on_storage_error(monkeypatch):
    mock_app = MagicMock()
    mock_app.storage.user.get = MagicMock(side_effect=RuntimeError("no storage"))
    monkeypatch.setattr("frontend.utils.storage.app", mock_app)
    assert read_pipeline_job_id() is None
