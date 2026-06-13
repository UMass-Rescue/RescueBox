"""Job record types shared by ``job_db`` and UI helpers (no SQLite)."""

import json
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from rb.api.models import RequestBody, ResponseBody, TaskSchema

from frontend.database.db_exceptions import DB_ERRORS
from frontend.database.validation import DatabaseValidator

logger = logging.getLogger(__name__)


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
    userId: Optional[str] = Field(
        None, description="NiceGUI session or user identifier"
    )
    modelUid: Optional[str] = Field(None, description="Model UID for traditional jobs")
    taskUid: Optional[str] = Field(None, description="Task UID for traditional jobs")
    endpoint: Optional[str] = Field(None, description="Endpoint name for chatbot jobs")
    endpointChain: Optional[List[str]] = Field(
        None,
        description="Ordered endpoints for multi-step chatbot pipelines (includes current job endpoint)",
    )
    pipelineRootJobId: Optional[str] = Field(
        None,
        description="Stable id for the first job in a multi-step pipeline; links sibling step jobs",
    )
    pipelineMetadataFilterCriteria: Optional[str] = Field(
        None,
        description="Classifier metadata filter (e.g. age/gender) applied when chaining to the next pipeline step",
    )
    filterId: Optional[str] = Field(
        None, description="Optional persisted filter id linking to file_filters"
    )
    caseNotes: Optional[str] = Field(
        None, description="User-entered case notes for the job"
    )
    startTime: str = Field(..., description="Job start time in ISO format")
    endTime: Optional[str] = Field(None, description="Job end time in ISO format")
    status: JobStatus = Field(..., description="Job status")
    statusText: Optional[str] = Field(None, description="Status text for errors")
    request: Union[RequestBody, Dict[str, Any]] = Field(..., description="Request body")
    response: Optional[Union[ResponseBody, Dict[str, Any]]] = Field(
        None, description="Response body"
    )
    taskSchema: Union[TaskSchema, Dict[str, Any]] = Field(
        ..., description="Task schema"
    )

    @field_validator("request", mode="before")
    @classmethod
    def validate_request(cls, v):
        """Convert dict to RequestBody if needed"""
        if isinstance(v, dict):
            try:
                return RequestBody(**v)
            except DB_ERRORS as e:
                logger.warning(
                    "Could not validate request as RequestBody, keeping as dict: %s", e
                )
                return v
        return v

    @field_validator("response", mode="before")
    @classmethod
    def validate_response(cls, v):
        """Convert dict to ResponseBody if needed"""
        if v is None:
            return None
        if isinstance(v, dict):
            try:
                return ResponseBody(**v)
            except DB_ERRORS as e:
                logger.warning(
                    "Could not validate response as ResponseBody, keeping as dict: %s",
                    e,
                )
                return v
        return v

    @field_validator("taskSchema", mode="before")
    @classmethod
    def validate_task_schema(cls, v):
        """Convert dict to TaskSchema if needed"""
        if isinstance(v, dict):
            try:
                return TaskSchema(**v)
            except DB_ERRORS as e:
                logger.warning(
                    "Could not validate taskSchema as TaskSchema, keeping as dict: %s",
                    e,
                )
                return v
        return v

    @field_validator("endpointChain", mode="before")
    @classmethod
    def validate_endpoint_chain(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, list):
            return [str(x) for x in v]
        if isinstance(v, str):
            try:
                data = json.loads(v)
                return [str(x) for x in data] if isinstance(data, list) else None
            except json.JSONDecodeError:
                return None
        return None

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        """Convert string to JobStatus if needed"""
        if isinstance(v, str):
            try:
                return JobStatus(v)
            except ValueError:
                for status in JobStatus:
                    if status.value.lower() == v.lower():
                        return status
                logger.warning("Unknown status: %s, using RUNNING", v)
                return JobStatus.RUNNING
        return v

    def model_dump_for_db(self) -> Dict[str, Any]:
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


__all__ = ["JobStatus", "JobRecord"]
