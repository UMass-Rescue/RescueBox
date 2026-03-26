"""
Unit tests for multi-step job pipelines: endpoint chains, job utils, and DB helpers.

Focuses on behavior introduced for chatbot tool chains without requiring NiceGUI.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from frontend.database import JobStatus, JobRecord
from frontend.pages.jobs.job_utils import extract_job_fields, compute_job_results_title
from rb.api.models import RequestBody, TaskSchema


def _minimal_request_and_schema():
    return (
        RequestBody(inputs={}, parameters={}),
        TaskSchema(inputs=[], parameters=[]),
    )


class TestComputeJobResultsTitle:
    def test_multi_step_chain_uses_arrow_join(self):
        title = compute_job_results_title(
            "text_embeddings/search",
            ["image_summary/summarize-images", "text_embeddings/search"],
        )
        assert title.startswith("Results for:")
        assert "→" in title
        assert "image_summary/summarize-images" in title
        assert "text_embeddings/search" in title

    def test_single_endpoint_in_chain(self):
        assert compute_job_results_title(None, ["audio/transcribe"]) == "Results for audio/transcribe"

    def test_fallback_to_endpoint_when_no_chain(self):
        assert compute_job_results_title("audio/transcribe", None) == "Results for audio/transcribe"
        assert compute_job_results_title("audio/transcribe", []) == "Results for audio/transcribe"

    def test_empty_without_endpoint(self):
        assert compute_job_results_title(None, None) == "Results"


class TestExtractJobFieldsEndpointChain:
    def test_job_record_includes_endpoint_chain(self):
        req, ts = _minimal_request_and_schema()
        rec = JobRecord(
            uid="JOB_abc123",
            startTime="2025-01-01T00:00:00",
            status=JobStatus.COMPLETED,
            request=req,
            taskSchema=ts,
            endpoint="step2",
            endpointChain=["step1", "step2"],
        )
        fields = extract_job_fields(rec)
        assert fields["endpointChain"] == ["step1", "step2"]
        assert fields["endpoint"] == "step2"

    def test_dict_legacy_includes_endpoint_chain(self):
        fields = extract_job_fields(
            {
                "uid": "u1",
                "endpoint": "a",
                "endpointChain": ["a", "b"],
                "status": "Completed",
                "request": {},
                "taskSchema": {},
            }
        )
        assert fields["endpointChain"] == ["a", "b"]


class TestJobRecordEndpointChainValidator:
    def test_list_normalized_to_strings(self):
        rec = JobRecord(
            uid="JOB_x",
            startTime="t",
            status=JobStatus.RUNNING,
            request=RequestBody(inputs={}, parameters={}),
            taskSchema=TaskSchema(inputs=[], parameters=[]),
            endpoint="e",
            endpointChain=["a", 2, "c"],
        )
        assert rec.endpointChain == ["a", "2", "c"]

    def test_json_string_parsed(self):
        rec = JobRecord(
            uid="JOB_x",
            startTime="t",
            status=JobStatus.RUNNING,
            request=RequestBody(inputs={}, parameters={}),
            taskSchema=TaskSchema(inputs=[], parameters=[]),
            endpoint="e",
            endpointChain=json.dumps(["x", "y"]),
        )
        assert rec.endpointChain == ["x", "y"]

    def test_invalid_json_string_becomes_none(self):
        rec = JobRecord(
            uid="JOB_x",
            startTime="t",
            status=JobStatus.RUNNING,
            request=RequestBody(inputs={}, parameters={}),
            taskSchema=TaskSchema(inputs=[], parameters=[]),
            endpoint="e",
            endpointChain="not-json",
        )
        assert rec.endpointChain is None


@pytest.mark.asyncio
class TestDatabaseServiceJobHelpers:
    async def test_create_and_track_job_passes_endpoint_chain_to_db(self):
        from frontend.pages.chatbot.utils import database_service as ds

        mock_job = MagicMock()
        mock_job.uid = "JOB_chain1"
        mock_job.modelUid = None
        captured = {}

        async def capture_create(**kwargs):
            captured.update(kwargs)
            return mock_job

        mock_db = MagicMock()
        mock_db.create_job = capture_create
        mock_db.update_job_status = AsyncMock()

        with patch.object(ds, "get_job_db", return_value=mock_db):
            with patch.object(ds, "set_logging_context", MagicMock()):
                out = await ds.DatabaseService.create_and_track_job(
                    RequestBody(inputs={}, parameters={}),
                    "text_embeddings/search",
                    task_schema=TaskSchema(inputs=[], parameters=[]),
                    endpoint_chain=["image_summary/summarize-images", "text_embeddings/search"],
                )

        assert out is not None
        assert captured.get("endpoint_chain") == [
            "image_summary/summarize-images",
            "text_embeddings/search",
        ]
        assert captured.get("endpoint") == "text_embeddings/search"

    async def test_update_job_status_accepts_string_completed(self):
        from frontend.pages.chatbot.utils import database_service as ds

        mock_db = MagicMock()
        mock_db.update_job_status = AsyncMock()

        with patch.object(ds, "get_job_db", return_value=mock_db):
            await ds.DatabaseService.update_job_status("JOB_x", "completed")

        mock_db.update_job_status.assert_called_once()
        call_kw = mock_db.update_job_status.call_args
        assert call_kw[1]["status"] == JobStatus.COMPLETED

