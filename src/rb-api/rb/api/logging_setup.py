"""
File logging for the standalone rb-api process (``python -m rb.api.main``).

Uses ``frontend.utils.logging_context`` for the same format and context filter as
the desktop app, but writes to a backend-specific path by default.

Environment:

- ``RESCUEBOX_API_LOG_FILE``: absolute or relative path to the log file.
  If unset, uses ``<rb/api>/data/rb-api.log`` (directory is created).
- ``RESCUEBOX_API_LOG_LEVEL``: ``DEBUG``, ``INFO``, etc.
  If unset, defaults to **DEBUG** so routes such as ``rb.api.routes.cli`` (which
  log most traffic at DEBUG) appear in the file and on stderr—matching typical
  pre-file-handler console verbosity. Uvicorn also applies its own logging config
  at server start; :func:`configure_backend_logging` is run again on FastAPI
  **startup** so root file + console handlers stay attached.

  Set ``RESCUEBOX_API_LOG_LEVEL=INFO`` for quieter logs. We intentionally do **not**
  fall back to ``RESCUEBOX_LOG_LEVEL`` here, so a desktop INFO default does not
  silence API DEBUG lines.
"""

from __future__ import annotations

import os
from pathlib import Path


def backend_log_file_path() -> Path:
    env = os.environ.get("RESCUEBOX_API_LOG_FILE")
    if env:
        return Path(env).expanduser().resolve()
    
    return Path("/home/tester/RescueBox/rb_backend.log").resolve()


def backend_log_level() -> str:
    return os.environ.get("RESCUEBOX_API_LOG_LEVEL") or "DEBUG"


def configure_backend_logging() -> None:
    """Install root file + console logging for the API process."""
    from frontend.utils.logging_context import configure_logging_with_context

    path = backend_log_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    configure_logging_with_context(
        log_file_path=str(path),
        log_level=backend_log_level(),
    )
