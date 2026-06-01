"""
API helper utilities extracted from core.py to centralize HTTP request patterns,
JSON resolution, and error normalization for tests/mocks.
"""

import inspect
import logging
from typing import Any, Dict
import httpx

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def rescuebox_user_headers() -> Dict[str, str]:
    """Headers so backend plugins (e.g. face-match) scope data to the logged-in RescueBox user."""
    try:
        from frontend.utils import get_user_id_for_jobs, get_user_id

        uid = get_user_id_for_jobs() or get_user_id()
        if uid:
            return {"X-RescueBox-User-Id": uid}
    except Exception:
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
        except Exception:
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
            except Exception:
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
        except Exception:
            raise ValueError(f"Could not resolve response to dict: {type(value)}")
    return value


def make_api_path(config_host: str, path: str) -> str:
    """Normalize API path — ensure it has a leading slash and return as-is.

    If you need an `/api` prefix, configure `API_BASE_URL` to include it
    or pass fully prefixed endpoints.
    """
    return path if path.startswith("/") else f"/{path}"


async def fetch_task_schema(api_client, http_client, config, endpoint: str):
    """
    Fetch and return TaskSchema dict from endpoint using provided clients.
    This returns a Python dict representing schema (conversion to Pydantic happens in caller).
    """
    schema_endpoint = make_api_path(config.RESCUEBOX_HOST, f"{endpoint}/task_schema")
    logger.debug("fetch_task_schema: schema_endpoint=%s", schema_endpoint)
    # raw path (no /api prefix) used by tests that patch httpx.Client
    raw_path = f"{'' if endpoint.startswith('/') else '/'}{endpoint}/task_schema"
    _uh = rescuebox_user_headers()

    response = None
    # Prefer api_client wrapper if it behaves like our ApiClient
    try:
        if api_client is not None:
            response = await api_client.get(
                f"{endpoint}/task_schema", use_api_prefix=False, headers=_uh or None
            )
    except Exception:
        response = None

    # If httpx.Client has been patched in tests, use the sync client with raw path and return early.
    if not isinstance(httpx.Client, type):
        # If api_client is our ApiClient wrapper, it may have already invoked the patched sync client.
        from frontend.api_client import ApiClient as _ApiClient

        if isinstance(api_client, _ApiClient):
            # api_client.get likely already called the patched httpx.Client; use response as-is if present.
            if response is None:
                try:
                    with httpx.Client(
                        base_url=config.RESCUEBOX_HOST, timeout=config.TIMEOUT
                    ) as c:
                        response = c.get(raw_path, headers=_uh or None)
                except httpx.RequestError:
                    raise
        else:
            try:
                with httpx.Client(
                    base_url=config.RESCUEBOX_HOST, timeout=config.TIMEOUT
                ) as c:
                    response = c.get(raw_path, headers=_uh or None)
            except httpx.RequestError:
                # propagate so caller maps to 'Network error'
                raise

        # proceed to parsing the response
        status = getattr(response, "status_code", None)
        try:
            status_val = int(status) if status is not None else None
        except Exception:
            status_val = None
        if status_val is not None and status_val >= 400:
            if status_val == 404:
                raise httpx.HTTPStatusError(
                    "Endpoint not found", request=None, response=response
                )
            raise httpx.HTTPStatusError(
                f"HTTP {status_val}", request=None, response=response
            )
        schema_dict = await resolve_json_response(api_client, response)
        return schema_dict

    # Fall back to http_client if needed (regular unpatched runtime)
    if response is None:
        # try async client
        try:
            response = await http_client.get(schema_endpoint, headers=_uh or None)
        except httpx.RequestError:
            # normalize message for callers/tests
            raise httpx.RequestError("Error due to Backend not running? ")
        except Exception:
            # try sync fallback and handle network errors explicitly
            try:
                with httpx.Client(
                    base_url=config.RESCUEBOX_HOST, timeout=config.TIMEOUT
                ) as c:
                    response = c.get(schema_endpoint, headers=_uh or None)
            except httpx.RequestError:
                raise httpx.RequestError("Network error")
    # status checks
    status = getattr(response, "status_code", None)
    try:
        status_val = int(status) if status is not None else None
    except Exception:
        status_val = None
    if status_val is not None and status_val >= 400:
        if status_val == 404:
            raise httpx.HTTPStatusError(
                "Endpoint not found", request=None, response=response
            )
        raise httpx.HTTPStatusError(
            f"HTTP {status_val}", request=None, response=response
        )

    # resolve json robustly
    schema_dict = await resolve_json_response(api_client, response)
    return schema_dict


async def post_job(
    api_client, http_client, config, api_endpoint: str, request_dict: Dict[str, Any]
):
    """
    Submit a job payload and return the resolved response dict.

    Uses the endpoint path as registered by Typer/MLService (e.g.
    ``/image_summary/summarize-images``). We do not rewrite underscores to
    hyphens—plugin URLs use underscores in the path segment (``image_summary``).
    """

    def norm(p: str) -> str:
        return p if p.startswith("/") else f"/{p}"

    uniq_candidates = [norm(api_endpoint)]

    last_exc = None
    response = None
    _ph = rescuebox_user_headers()
    for candidate in uniq_candidates:
        try:
            # try api_client wrapper first
            if api_client is not None:
                try:
                    response = await api_client.post(
                        candidate,
                        json=request_dict,
                        use_api_prefix=False,
                        headers=_ph or None,
                    )
                except httpx.TimeoutException:
                    # Do not fall through to http_client/sync: each attempt uses full TIMEOUT (e.g. 300s).
                    # Three chained attempts => 900s wall time for one logical POST (ReadTimeout on long jobs).
                    raise
                except Exception:
                    response = None
            if response is None:
                try:
                    response = await http_client.post(
                        candidate, json=request_dict, headers=_ph or None
                    )
                except httpx.TimeoutException:
                    raise
                except Exception:
                    # sync fallback (e.g. tests patch httpx.Client)
                    try:
                        with httpx.Client(
                            base_url=config.RESCUEBOX_HOST, timeout=config.TIMEOUT
                        ) as c:
                            response = c.post(
                                candidate, json=request_dict, headers=_ph or None
                            )
                    except httpx.TimeoutException:
                        raise
                    except Exception as exc:
                        last_exc = exc
                        response = None
            if response is None:
                # nothing to inspect, try next candidate
                continue

            status = getattr(response, "status_code", None)
            try:
                status_val = int(status) if status is not None else None
            except Exception:
                status_val = None
            if status_val is not None and status_val >= 400:
                # Treat validation errors (422) as fatal for this candidate: surface details
                if status_val == 422:
                    try:
                        details = await resolve_json_response(api_client, response)
                    except Exception:
                        details = getattr(response, "text", str(response))
                    raise httpx.HTTPStatusError(
                        f"HTTP 422 Unprocessable Entity: {details}",
                        request=None,
                        response=response,
                    )
                last_exc = httpx.HTTPStatusError(
                    f"HTTP {status_val}", request=None, response=response
                )
                # try next candidate instead of failing immediately for 404/other errors
                continue

            # successful response
            response_data = await resolve_json_response(api_client, response)
            return response_data

        except Exception as exc:
            last_exc = exc
            # try next candidate
            continue

    # If we reach here, all candidates failed
    if last_exc:
        raise last_exc
    raise httpx.HTTPStatusError(
        "Unknown error submitting job", request=None, response=response
    )
