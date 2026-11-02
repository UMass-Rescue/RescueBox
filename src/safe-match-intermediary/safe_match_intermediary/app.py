"""HTTP API of the Safe Match intermediary: validate, queue uploads, proxy queries."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import __version__
from .config import Credentials, CredentialsError, Settings, load_credentials
from .outbox import Outbox, Worker
from .remote import Remote, RemoteError
from .schemas import InvalidRequest, validate_query, validate_upload
from .stub import STUB_CREDENTIALS, FakeApi

logger = logging.getLogger(__name__)
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
MAX_BODY_BYTES = 64 * 1024
REMOTE_ERRORS = {
    "unauthorized": (
        "remote_unauthorized",
        "UMass rejected this server's credentials.",
    ),
    "forbidden": ("remote_forbidden", "This server's credentials lack a needed scope."),
    "unavailable": ("remote_unavailable", "UMass Safe Matching is unavailable; retry."),
}
router = APIRouter()


class ApiError(Exception):
    """An error response whose message never repeats request values."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        fields: list[str] | None = None,
        request_id: str | None = None,
    ):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message
        self.fields, self.request_id = fields or [], request_id


@dataclass
class Services:
    settings: Settings
    outbox: Outbox
    remote: Remote | None
    worker: Worker | None
    problem: str | None


def create_app(
    settings: Settings, transport: httpx.AsyncBaseTransport | None = None
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with _running(settings, transport) as services:
            app.state.services = services
            yield

    app = FastAPI(debug=False, openapi_url=None, lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
    app.middleware("http")(_catch_all)
    app.add_exception_handler(ApiError, _error_response)
    app.include_router(router)
    return app


@asynccontextmanager
async def _running(
    settings: Settings, transport: httpx.AsyncBaseTransport | None
) -> AsyncIterator[Services]:
    credentials, problem = _credentials(settings)
    if settings.mode == "stub":
        transport = transport or httpx.MockTransport(FakeApi())
    timeout = httpx.Timeout(30, connect=5)
    async with httpx.AsyncClient(transport=transport, timeout=timeout) as http:
        stub = settings.mode == "stub"
        outbox = Outbox(None if stub else settings.data_dir / "outbox.db")
        remote = Remote(credentials, http) if credentials else None
        worker = Worker(outbox, remote) if remote else None
        jobs = [worker.run(), remote.check()] if worker and remote else []
        tasks = [asyncio.create_task(job) for job in jobs]
        try:
            yield Services(settings, outbox, remote, worker, problem)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            outbox.close()


def _credentials(settings: Settings) -> tuple[Credentials | None, str | None]:
    if settings.mode == "stub":
        return STUB_CREDENTIALS, None
    try:
        return load_credentials(settings.credentials_path), None
    except CredentialsError as error:
        logger.warning("credentials_%s %s", error.reason, error)
        return None, f"credentials_{error.reason}"


@router.post("/v1/upload", status_code=202)
async def upload(request: Request) -> dict:
    services = _configured(request)
    item = await read_json(request, validate_upload)
    services.outbox.put(item)
    services.worker.wake.set()
    return {
        "sha256": item["sha256"],
        "essay_version": item["essay_version"],
        "delivery": "queued",
    }


@router.post("/v1/query")
async def query(request: Request) -> dict:
    services = _configured(request)
    item = await read_json(request, validate_query)
    try:
        return await services.remote.query(item)
    except RemoteError as error:
        raise _from_remote(error) from None


@router.get("/v1/status")
async def status(request: Request) -> dict:
    services: Services = request.app.state.services
    remote = services.problem or services.remote.state
    return {
        "service": "safe-match-intermediary",
        "version": __version__,
        "mode": services.settings.mode,
        "configured": services.remote is not None,
        "remote": remote,
        "outbox": services.outbox.counts(),
    }


async def read_json(request: Request, validate: Callable[[object], dict]) -> dict:
    """Parse a JSON body; other media types could be sent cross-site without CORS."""
    media_type = request.headers.get("content-type", "").split(";")[0].strip()
    if media_type.lower() != "application/json":
        raise ApiError(415, "unsupported_media_type", "Send application/json.")
    try:
        body = json.loads(await _body(request))
    except ValueError:
        raise ApiError(400, "invalid_json", "The body must be valid JSON.") from None
    try:
        return validate(body)
    except InvalidRequest as error:
        raise ApiError(400, "invalid_request", error.message, error.fields) from None


async def _body(request: Request) -> bytes:
    body = b""
    async for chunk in request.stream():
        body += chunk
        if len(body) > MAX_BODY_BYTES:
            raise ApiError(413, "payload_too_large", "The request body is too large.")
    return body


def _configured(request: Request) -> Services:
    services: Services = request.app.state.services
    if services.remote is None:
        message = "Safe Match has no valid UMass credentials; ask your administrator."
        raise ApiError(503, "not_configured", message)
    return services


def _from_remote(error: RemoteError) -> ApiError:
    if error.kind == "rejected":
        status = error.status or 400
        return ApiError(
            status, error.code, error.message, error.fields, error.request_id
        )
    code, message = REMOTE_ERRORS[error.kind]
    return ApiError(503, code, message, request_id=error.request_id)


async def _error_response(request: Request, error: ApiError) -> JSONResponse:
    body: dict = {"code": error.code, "message": error.message}
    if error.fields:
        body["details"] = {"fields": error.fields}
    if error.request_id:
        body["request_id"] = error.request_id
    return JSONResponse({"error": body}, status_code=error.status)


async def _catch_all(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Log only the exception type: messages and tracebacks can hold request data."""
    try:
        return await call_next(request)
    except Exception as error:
        logger.error("request_failed %s", type(error).__name__)
        body = {"error": {"code": "internal_error", "message": "Unexpected failure."}}
        return JSONResponse(body, status_code=500)
