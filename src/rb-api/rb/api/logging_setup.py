"""
File logging for the standalone rb-api process (``python -m rb.api.main``).

Uses ``frontend.utils.logging_context`` for the same format and context filter as
the desktop app, but writes to a backend-specific path by default.

Environment:

- ``RESCUEBOX_API_LOG_FILE``: absolute or relative path to the log file.
  If unset, uses ``rb/api/data/rb-api.log`` next to this package (directory is created).
- ``RESCUEBOX_API_LOG_LEVEL``: ``DEBUG``, ``INFO``, etc.
  If unset, defaults to **DEBUG**. At **INFO**, you still get one **INFO** line per
  plugin request (see ``rb.api.routes.cli``) plus Uvicorn access lines; detailed
  request/response traces stay at **DEBUG**. Without that, it can look like logging
  "stopped" after startup because SQLAlchemy only logs heavily during migrations.

  Uvicorn applies its own logging config when the server starts;
  :func:`configure_backend_logging` runs at import and again on FastAPI **startup**
  so root file + console handlers stay attached.

  Set ``RESCUEBOX_API_LOG_LEVEL=INFO`` for quieter logs. We intentionally do **not**
  fall back to ``RESCUEBOX_LOG_LEVEL`` here, so a desktop INFO default does not
  silence API DEBUG lines.

- ``RESCUEBOX_API_SQLALCHEMY_LOG_LEVEL``: default **WARNING** so engine/pool INFO and
  DEBUG lines (SQL echo, pool checkout/return) do not flood the console or log file.
  Set to ``INFO`` or ``DEBUG`` only when diagnosing DB issues.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path


def backend_log_file_path() -> Path:
    env = os.environ.get("RESCUEBOX_API_LOG_FILE")
    if env:
        return Path(env).expanduser().resolve()
    logfile =Path("rb-backend.log")
    return logfile


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
    level = logging.WARNING
    for name in (
        "sqlalchemy",
        "sqlalchemy.engine",
        "sqlalchemy.engine.Engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
        "sqlalchemy.orm",
    ):
        logging.getLogger(name).setLevel(level)
