"""
Backend FastAPI route integration and startup tasks for the unified NiceGUI server.

Keeps ``frontend.main`` focused on UI route registration and ``ui.run``.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Set by main after import attempt
BACKEND_AVAILABLE: bool = False


def set_backend_available(available: bool) -> None:
    global BACKEND_AVAILABLE
    BACKEND_AVAILABLE = available


def check_backend_running(backend_url: str = "http://localhost:8000", timeout: float = 1.0) -> bool:
    """Return True if a backend responds to the liveness probe."""
    try:
        response = httpx.get(f"{backend_url}/probes/liveness/", timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def setup_backend_routes(
    *,
    api_base_url: str,
    use_external_backend: bool = False,
) -> None:
    """
    Integrate backend FastAPI routes into NiceGUI's FastAPI app when the rb.api
    package is available and external-backend mode is not requested.
    """
    if not BACKEND_AVAILABLE:
        logger.warning("Skipping backend route integration - backend not available")
        return

    from nicegui import app
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi import Request, status, HTTPException
    from fastapi.exceptions import RequestValidationError

    use_external = (
        use_external_backend
        or os.getenv("RESCUEBOX_USE_EXTERNAL_BACKEND", "").lower() == "true"
    )
    if use_external:
        logger.info("Using external backend (route integration skipped)")
        logger.info("Frontend will connect to backend at: %s", api_base_url)
        return

    check_external = os.getenv("RESCUEBOX_CHECK_EXTERNAL_BACKEND", "false").lower() == "true"
    if check_external:
        external_backend_url = api_base_url
        if check_backend_running(external_backend_url):
            logger.info(
                "External backend detected at %s - skipping route integration",
                external_backend_url,
            )
            logger.info("Frontend will connect to external backend instead of integrated routes")
            return

    logger.info("Integrating backend FastAPI routes into NiceGUI app")

    from rb.api import routes

    fastapi_app = app

    cors_exists = any(
        isinstance(middleware, CORSMiddleware) for middleware in fastapi_app.user_middleware
    )
    if not cors_exists:
        fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("Added CORS middleware")

    try:
        from rb.api.facematch_request_context import FacematchRescueboxUserMiddleware

        fastapi_app.add_middleware(FacematchRescueboxUserMiddleware)
    except ImportError:
        pass

    @fastapi_app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        error_msg = str(exc)
        for e in exc.errors():
            error_msg = e.get("msg")

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": f"{error_msg}"},
        )

    fastapi_app.include_router(routes.probes_router, prefix="/api/probes")
    fastapi_app.include_router(routes.cli_to_api_router, prefix="/api")
    fastapi_app.include_router(routes.models_router, prefix="/api")

    logger.info("Backend routes integrated successfully")
    logger.info("Backend API available at: /models, /probes, /{endpoint}/*, etc.")


async def prefetch_and_cache_models(
    *,
    backend_url: str,
    api_timeout: float,
) -> None:
    """Pre-fetch models from the backend on startup and cache them in SQLite."""
    from frontend.database import cache_models

    logger.info("Attempting to pre-fetch and cache models on application startup...")
    loop = asyncio.get_event_loop()

    def fetch_sync() -> Optional[object]:
        try:
            with httpx.Client(base_url=backend_url, timeout=api_timeout) as client:
                response = client.get("/api/models")
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()
                logger.debug("Models API response status: %s", response.status_code)
                logger.debug("Models API response content type: %s", content_type)
                logger.debug("Models API response content length: %s", len(response.content))

                if "application/json" not in content_type:
                    logger.warning("Models API returned non-JSON content type: %s", content_type)
                    if response.content:
                        logger.warning("Response content preview: %s...", response.content[:200])
                    return None

                if not response.content.strip():
                    logger.warning("Models API returned empty response")
                    return None

                try:
                    return response.json()
                except ValueError as json_error:
                    logger.error("Failed to parse JSON response: %s", json_error)
                    logger.error("Raw response content: %s...", response.content[:500])
                    return None

        except Exception as e:
            logger.error("Synchronous fetch in executor failed: %s", e)
            return None

    try:
        models_data = await loop.run_in_executor(None, fetch_sync)
        if models_data:
            logger.info("Successfully pre-fetched %s models from the backend.", len(models_data))
            await cache_models(models_data)
        else:
            logger.warning("Pre-fetching models returned no data. Skipping cache update.")
    except Exception as e:
        logger.error("Failed to pre-fetch models during startup: %s", e)
