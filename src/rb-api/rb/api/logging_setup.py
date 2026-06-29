"""
File logging for the standalone rb-api process (``python -m rb.api.main``).

Uses ``frontend.utils.logging_context`` for the same format and context filter as
the desktop app, but writes to a backend-specific path by default.

"""

from __future__ import annotations

import logging
import os
import platform
from pathlib import Path


def backend_log_file_path() -> Path:
    env = os.environ.get("RESCUEBOX_API_LOG_FILE")
    if env:
        return Path(env).expanduser().resolve()
    logfile = Path("rb-backend.log")
    if platform.system() == "Windows":
        base_dir = Path(os.getenv("APPDATA"))
        logfile = base_dir / "RescueBox-Desktop" / "logs" / "backend.log"

    return logfile


def backend_log_level() -> str:
    return os.environ.get("RESCUEBOX_API_LOG_LEVEL") or "INFO"


def configure_backend_logging() -> None:
    """Install root file + console logging for the API process."""
    from frontend.utils import configure_logging_with_context

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

    # Uvicorn's default log_config sets disable_existing_loggers=True.
    # Re-enable any plugin loggers that were imported before Uvicorn started.
    for name, logger_instance in list(logging.root.manager.loggerDict.items()):
        if isinstance(logger_instance, logging.Logger):
            logger_instance.disabled = False
