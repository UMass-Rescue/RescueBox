"""
Centralized per-logger level tuning for the RescueBox frontend.

When the effective log level is DEBUG, the root logger is verbose but known-noisy
libraries (socket.io, httpx, NiceGUI internals, etc.) are capped to WARNING, while
pipeline/orchestration namespaces stay at INFO for useful diagnostics.

Used from :func:`frontend.utils.logging_context.configure_logging_with_context`.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

# Third-party and internal loggers that flood output at DEBUG.
_NOISY_WARNING_NAMES: tuple[str, ...] = (
    "socketio.server",
    "socketio",
    "engineio.server",
    "engineio",
    "fuse",
    "fuse.log-mixin",
    "ufdr_mounter.utils.ufdr_mount_unix",
    "frontend.pages.chatbot",
    "frontend.database.chat_history_db",
    "frontend.utils.nicegui_storage",
    "httpcore",
    "httpcore.http11",
    "httpx",
    "frontend.chatbot",
    "frontend.components.forms",
    "frontend.components.results.tool_selection_card",
    "frontend.utils.validators",
    "frontend.utils.file_browser",
    "nicegui",
)

# Additional chatbot/forms modules (per-module DEBUG overrides parent).
_CHATBOT_FORMS_WARNING_NAMES: tuple[str, ...] = (
    "frontend.pages.chatbot.chatbot_forms",
    "frontend.pages.chatbot.chatbot",
    "frontend.pages.chatbot.state.state_manager",
    "frontend.pages.chatbot.utils.form_validator",
    "frontend.components.forms.form_generator",
    "frontend.components.forms.form_handlers",
    "frontend.components.forms.builders.input_field_builder",
    "frontend.components.forms.case_notes_dialog",
)

# Must stay INFO when parent namespaces are WARNING (multi-tool pipeline visibility).
_PIPELINE_DIAG_INFO_NAMES: tuple[str, ...] = (
    "frontend.pages.chatbot.utils.job_submission_orchestrator",
    "frontend.chatbot.multi_tool_handler",
)


def effective_debug_requested(config_log_level: str) -> bool:
    """True if we should apply DEBUG-style noise quieting (config or env)."""
    if config_log_level.upper() == "DEBUG":
        return True
    try:
        return os.getenv("LOG_LEVEL", "").upper() == "DEBUG"
    except Exception:
        return False


def apply_per_logger_levels_for_verbose_root(config_log_level: str) -> None:
    """
    After root is set to DEBUG, quiet noisy loggers and restore pipeline INFO.

    Safe to call multiple times; failures are ignored (best-effort).
    """
    if not effective_debug_requested(config_log_level):
        return
    try:
        mgr = getattr(logging, "manager", None) or getattr(
            logging.getLogger(), "manager", None
        )
        if mgr is not None and hasattr(mgr, "loggerDict"):
            for _name, logger_obj in list(mgr.loggerDict.items()):
                if isinstance(logger_obj, logging.Logger):
                    try:
                        logger_obj.setLevel(logging.NOTSET)
                    except Exception:
                        pass
        for noisy in _NOISY_WARNING_NAMES:
            logging.getLogger(noisy).setLevel(logging.WARNING)
        for noisy in _CHATBOT_FORMS_WARNING_NAMES:
            logging.getLogger(noisy).setLevel(logging.WARNING)
        for name in _PIPELINE_DIAG_INFO_NAMES:
            logging.getLogger(name).setLevel(logging.INFO)
    except Exception:
        pass


def parse_log_level(name: Optional[str], default: int = logging.INFO) -> int:
    """Resolve a level name (e.g. from ``RESCUEBOX_LOG_LEVEL``) to ``logging`` int."""
    if not name:
        return default
    level = getattr(logging, str(name).upper(), None)
    return level if isinstance(level, int) else default
