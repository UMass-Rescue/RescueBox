"""Job record types shared by ``job_db`` and UI helpers (no SQLite)."""

import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from rb.api.models import RequestBody, ResponseBody, TaskSchema

from frontend.database.validation import DatabaseValidator


class JobStatus(str, Enum):
    """Job status enumeration"""

    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELED = "Canceled"


class JobRecord(BaseModel):
    """
    Pydantic model for job records in the database.

    Represents a job with all its metadata, request, response, and schema.
    Supports both traditional model/task jobs and chatbot endpoint-based jobs.
    """

    uid: str = Field(..., description="Unique job identifier")
    userId: str | None = Field(
        default=None, description="NiceGUI session or user identifier"
    )
    modelUid: str | None = Field(
        default=None, description="Model UID for traditional jobs"
    )
    taskUid: str | None = Field(
        default=None, description="Task UID for traditional jobs"
    )
    endpoint: str | None = Field(
        default=None, description="Endpoint name for chatbot jobs"
    )
    endpointChain: list[str] | None = Field(
        default=None,
        description="Ordered endpoints for multi-step chatbot pipelines (includes current job endpoint)",
    )
    pipelineRootJobId: str | None = Field(
        default=None,
        description="Stable id for the first job in a multi-step pipeline; links sibling step jobs",
    )
    pipelineMetadataFilterCriteria: str | None = Field(
        default=None,
        description="Classifier metadata filter (e.g. age/gender) applied when chaining to the next pipeline step",
    )
    filterId: str | None = Field(
        default=None, description="Optional persisted filter id linking to file_filters"
    )
    caseNotes: str | None = Field(
        default=None, description="User-entered case notes for the job"
    )
    startTime: str = Field(..., description="Job start time in ISO format")
    endTime: str | None = Field(default=None, description="Job end time in ISO format")
    status: JobStatus = Field(..., description="Job status")
    statusText: str | None = Field(default=None, description="Status text for errors")
    request: RequestBody | dict[str, Any] = Field(..., description="Request body")
    response: ResponseBody | dict[str, Any] | None = Field(
        default=None, description="Response body"
    )
    taskSchema: TaskSchema | dict[str, Any] = Field(..., description="Task schema")

    def model_dump_for_db(self) -> dict[str, Any]:
        """Convert JobRecord to dict for database storage."""
        data = self.model_dump(mode="json")

        validator = DatabaseValidator()

        data["request"] = validator.serialize_json(data.get("request"))
        data["response"] = (
            validator.serialize_json(data.get("response"))
            if data.get("response")
            else None
        )
        data["taskSchema"] = validator.serialize_json(data.get("taskSchema"))

        if isinstance(data.get("status"), JobStatus):
            data["status"] = data["status"].value
        if "filterId" not in data:
            data["filterId"] = None
        if "caseNotes" not in data:
            data["caseNotes"] = None
        if "pipelineRootJobId" not in data:
            data["pipelineRootJobId"] = None
        if data.get("endpointChain") is not None:
            data["endpointChain"] = json.dumps(data["endpointChain"])
        else:
            data["endpointChain"] = None

        return data

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)


__all__ = ["JobRecord", "JobStatus"]
