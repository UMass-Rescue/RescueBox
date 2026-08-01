"""Request-scoped RescueBox job id (from ``X-RescueBox-Job-Id``) for progress reporting."""

from __future__ import annotations

from contextvars import ContextVar, Token

RESCUEBOX_JOB_HEADER = "x-rescuebox-job-id"

_current_job_id: ContextVar[str | None] = ContextVar("rescuebox_job_id", default=None)


def bind_job_id(job_id: str | None) -> Token:
    return _current_job_id.set(job_id)


def get_current_job_id() -> str | None:
    return _current_job_id.get()


def reset_job_id(token: Token) -> None:
    _current_job_id.reset(token)


def set_current_job_id(job_id: str | None) -> Token:
    """Legacy alias for :func:`bind_job_id`."""
    return bind_job_id(job_id)


reset_current_job_id = reset_job_id
