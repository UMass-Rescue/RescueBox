"""Submit RescueBox jobs via the HTTP API and normalize responses."""

import inspect
import logging
from typing import Any

import httpx
from rb.api.models import ResponseBody

from frontend.chatbot.api_helpers import post_job
from frontend.chatbot.exceptions import CHATBOT_ERRORS
from frontend.chatbot.multi_tool_handler import coerce_pipeline_response
from frontend.utils import get_user_id_for_jobs

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def submit_job_orchestrator(
    api_wrapper,
    http_client,
    config,
    request_body_dict: dict[str, Any],
    api_endpoint: str,
    job_id: str | None = None,
) -> ResponseBody:
    """
    Orchestrate job submission using api_helpers.post_job and normalize the response
    into a ResponseBody pydantic model.
    """
    if not get_user_id_for_jobs():
        raise RuntimeError("Set a demo User ID (demo_???) before submitting jobs.")

    logger.info("Orchestrating job execution for %s", api_endpoint)
    try:
        response_data = await post_job(
            api_wrapper, http_client, config, api_endpoint, request_body_dict, job_id
        )
    except httpx.HTTPStatusError as e:
        status = getattr(e.response, "status_code", None)
        detail_text = None
        try:
            err_j = e.response.json()
            if inspect.isawaitable(err_j):
                err_j = await err_j
            if isinstance(err_j, dict):
                detail_text = err_j.get("detail")
        except CHATBOT_ERRORS:
            detail_text = None
        if status == 500:
            raise RuntimeError(detail_text or "Internal server error") from e
        if status == 404:
            # keep stable prefix expected by tests
            raise RuntimeError(
                f'Job submission failed: {detail_text or "Not Found"}'
            ) from e
        raise RuntimeError(
            detail_text or f"Job submission failed: HTTP {status}"
        ) from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error submitting job: {e!s}") from e

    # Normalize mappings to plain dict if needed
    if inspect.isawaitable(response_data):
        response_data = await response_data

    if not isinstance(response_data, dict):
        # try common conversions
        if hasattr(response_data, "model_dump"):
            response_data = response_data.model_dump()
        elif hasattr(response_data, "dict"):
            response_data = response_data.dict()
        else:
            try:
                response_data = dict(response_data)
            except CHATBOT_ERRORS as exc:
                raise ValueError("Could not coerce job response to dict") from exc

    # Build ResponseBody model (coercion handles legacy / batchfile wire shapes)
    response_body = coerce_pipeline_response(response_data)
    if not isinstance(response_body, ResponseBody):
        response_body = ResponseBody(**response_data)
    return response_body
