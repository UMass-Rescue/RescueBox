"""
API helper utilities extracted from core.py to centralize HTTP request patterns,
JSON resolution, and error normalization for tests/mocks.
"""

import inspect
import logging
from typing import Any, Dict, Optional
import httpx

from frontend.api_client import ApiClient as _ApiClient
from frontend.utils import get_user_id, get_user_id_for_jobs
from frontend.chatbot.exceptions import CHATBOT_ERRORS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def rescuebox_user_headers() -> Dict[str, str]:
    """Headers so backend plugins (e.g. face-match) scope data to the logged-in RescueBox user."""
    try:
        uid = get_user_id_for_jobs() or get_user_id()
        if uid:
            return {"X-RescueBox-User-Id": uid}
    except CHATBOT_ERRORS:
        pass
    return {}


async def resolve_json_response(api_wrapper, response) -> Dict[str, Any]:
    """
    Robustly resolve a response's JSON payload handling awaitables, callables,
    and common mock wrappers.
    """
    # Prefer ApiClient.json if available and api_wrapper provided
    if api_wrapper is not None:
        try:
            return await api_wrapper.json(response)
        except CHATBOT_ERRORS:
            pass

    # Try common patterns
    maybe = getattr(response, "json", None)
    if not callable(maybe):
        if inspect.isawaitable(maybe):
            return await maybe
        return maybe

    value = maybe()
    attempts = 0
    while attempts < 10:
        if inspect.isawaitable(value):
            value = await value
            # unwrap AsyncMock-like return_value if present
            if hasattr(value, "return_value"):
                value = getattr(value, "return_value")
            attempts += 1
            continue
        if callable(value) and not isinstance(value, dict):
            try:
                value = value()
                if hasattr(value, "return_value"):
                    value = getattr(value, "return_value")
                attempts += 1
                continue
            except CHATBOT_ERRORS:
                break
        break

    # Final coercions
    if not isinstance(value, dict):
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if hasattr(value, "dict"):
            return value.dict()
        if hasattr(value, "to_dict"):
            return value.to_dict()
        try:
            return dict(value)
        except CHATBOT_ERRORS as exc:
            raise ValueError(
                f"Could not resolve response to dict: {type(value)}"
            ) from exc
    return value


def make_api_path(path: str) -> str:
    """Normalize API path — ensure it has a leading slash and return as-is."""
    return path if path.startswith("/") else f"/{path}"


def _http_status_code(response) -> Optional[int]:
    status = getattr(response, "status_code", None)
    if status is None:
        return None
    try:
        return int(status)
    except CHATBOT_ERRORS:
        return None


async def _post_via_clients(
    api_client,
    http_client,
    config,
    path: str,
    request_dict: Dict[str, Any],
    headers: Optional[Dict[str, str]],
):
    response = None
    if api_client is not None:
        try:
            response = await api_client.post(
                path,
                json=request_dict,
                use_api_prefix=False,
                headers=headers or None,
            )
        except CHATBOT_ERRORS:
            response = None
    if response is not None:
        return response
    try:
        return await http_client.post(path, json=request_dict, headers=headers or None)
    except CHATBOT_ERRORS:
        with httpx.Client(base_url=config.RESCUEBOX_HOST, timeout=config.TIMEOUT) as c:
            return c.post(path, json=request_dict, headers=headers or None)


async def _get_via_clients(
    api_client,
    http_client,
    config,
    api_relative_path: str,
    prefixed_path: str,
    headers: Optional[Dict[str, str]],
):
    """GET task schema path via ApiClient, async httpx, or sync httpx fallback."""
    response = None
    if api_client is not None:
        try:
            response = await api_client.get(
                api_relative_path,
                use_api_prefix=False,
                headers=headers or None,
            )
        except CHATBOT_ERRORS:
            response = None

    if not isinstance(httpx.Client, type):
        raw_path = (
            prefixed_path if prefixed_path.startswith("/") else f"/{prefixed_path}"
        )
        if isinstance(api_client, _ApiClient):
            if response is None:
                with httpx.Client(
                    base_url=config.RESCUEBOX_HOST, timeout=config.TIMEOUT
                ) as client:
                    response = client.get(raw_path, headers=headers or None)
        else:
            with httpx.Client(
                base_url=config.RESCUEBOX_HOST, timeout=config.TIMEOUT
            ) as client:
                response = client.get(raw_path, headers=headers or None)
        return response

    if response is not None:
        return response

    try:
        return await http_client.get(prefixed_path, headers=headers or None)
    except httpx.RequestError as exc:
        raise httpx.RequestError("Error due to Backend not running? ") from exc
    except CHATBOT_ERRORS:
        try:
            with httpx.Client(
                base_url=config.RESCUEBOX_HOST, timeout=config.TIMEOUT
            ) as client:
                return client.get(prefixed_path, headers=headers or None)
        except httpx.RequestError as exc:
            raise httpx.RequestError("Network error") from exc


def _raise_for_http_response(response) -> None:
    status_val = _http_status_code(response)
    if status_val is None or status_val < 400:
        return
    if status_val == 404:
        raise httpx.HTTPStatusError(
            "Endpoint not found", request=None, response=response
        )
    raise httpx.HTTPStatusError(f"HTTP {status_val}", request=None, response=response)


async def fetch_task_schema(api_client, http_client, config, endpoint: str):
    """
    Fetch and return TaskSchema dict from endpoint using provided clients.
    This returns a Python dict representing schema (conversion to Pydantic happens in caller).
    """
    schema_endpoint = make_api_path(f"{endpoint}/task_schema")
    logger.debug("fetch_task_schema: schema_endpoint=%s", schema_endpoint)
    headers = rescuebox_user_headers()
    api_relative_path = f"{endpoint}/task_schema"

    response = await _get_via_clients(
        api_client,
        http_client,
        config,
        api_relative_path,
        schema_endpoint,
        headers,
    )
    _raise_for_http_response(response)
    return await resolve_json_response(api_client, response)


async def post_job(
    api_client, http_client, config, api_endpoint: str, request_dict: Dict[str, Any]
):
    """
    Submit a job payload and return the resolved response dict.

    Uses the endpoint path as registered by Typer/MLService (e.g.
    ``/image_summary/summarize-images``). We do not rewrite underscores to
    hyphens—plugin URLs use underscores in the path segment (``image_summary``).
    """

    path = make_api_path(api_endpoint)
    headers = rescuebox_user_headers()
    last_exc = None
    response = None

    try:
        response = await _post_via_clients(
            api_client, http_client, config, path, request_dict, headers
        )
    except CHATBOT_ERRORS as exc:
        last_exc = exc
        response = None

    if response is None:
        if last_exc:
            raise last_exc
        raise httpx.HTTPStatusError(
            "Unknown error submitting job", request=None, response=response
        )

    status_val = _http_status_code(response)
    if status_val is not None and status_val >= 400:
        if status_val == 422:
            try:
                details = await resolve_json_response(api_client, response)
            except CHATBOT_ERRORS:
                details = getattr(response, "text", str(response))
            logger.info("backend response error =%s", details)
            raise httpx.HTTPStatusError(
                f"HTTP 422 Unprocessable Entity: {details}",
                request=None,
                response=response,
            )
        logger.info("backend response error = %s", str(response))
        raise httpx.HTTPStatusError(
            f"HTTP {status_val}", request=None, response=response
        )
    logger.info("backend response code=%d", status_val)
    return await resolve_json_response(api_client, response)
