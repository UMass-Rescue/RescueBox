"""Bind ``X-RescueBox-Job-Id`` to :mod:`rb.lib.job_progress_context` for plugin requests."""

from rb.lib import job_progress_context
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class JobProgressMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        job_id = request.headers.get(job_progress_context.RESCUEBOX_JOB_HEADER)
        if not job_id:
            return await call_next(request)
        token = job_progress_context.bind_job_id(job_id)
        try:
            return await call_next(request)
        finally:
            job_progress_context.reset_job_id(token)
