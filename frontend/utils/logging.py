import contextvars
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from frontend.config import LOG_FILE
from frontend.database.chat_history_db import get_chat_history_db
from frontend.database.job_db import get_job_db
from frontend.utils.exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)

# Context variables for tracking IDs
_job_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "job_id", default=None
)
_model_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "model_id", default=None
)
_session_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "session_id", default=None
)

# Noisy loggers configuration
_NOISY_WARNING_NAMES = (
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
    "frontend.components.results.tool_selection",
    "frontend.utils.validators",
    "frontend.utils.file_browser",
    "nicegui",
)

_CHATBOT_FORMS_WARNING_NAMES = (
    "frontend.pages.chatbot.chatbot_forms",
    "frontend.pages.chatbot.chatbot",
    "frontend.pages.chatbot.state.state_manager",
    "frontend.pages.chatbot.utils.form_validator",
    "frontend.components.forms.form_generator",
    "frontend.components.forms.form_generator",
    "frontend.components.forms.builders.input_field_builder",
    "frontend.components.forms.case_notes_dialog",
)

_PIPELINE_DIAG_INFO_NAMES = (
    "frontend.pages.chatbot.utils.job_submission_orchestrator",
    "frontend.chatbot.multi_tool_handler",
)


def set_logging_context(job_id=None, model_id=None, session_id=None):
    if job_id is not None:
        _job_id.set(job_id)
    if model_id is not None:
        _model_id.set(model_id)
    if session_id is not None:
        _session_id.set(session_id)


def get_logging_context():
    return {
        "job_id": _job_id.get(None),
        "model_id": _model_id.get(None),
        "session_id": _session_id.get(None),
    }


def clear_logging_context():
    _job_id.set(None)
    _model_id.set(None)
    _session_id.set(None)


class ContextFilter(logging.Filter):
    def filter(self, record):
        try:
            jid, mid, sid = (
                _job_id.get(None),
                _model_id.get(None),
                _session_id.get(None),
            )
            record.job_id, record.model_id, record.session_id = (
                jid or "-",
                mid or "-",
                sid or "-",
            )
            parts = []
            if jid:
                parts.append(f"job_id={jid}")
            if mid:
                parts.append(f"model_id={mid}")
            if sid:
                parts.append(f"session_id={sid}")
            record.context = f" | {' | '.join(parts)}" if parts else ""
        except UI_RENDER_ERRORS:
            record.job_id = record.model_id = record.session_id = "-"
            record.context = ""
        return True

    @staticmethod
    def reset_record_context(record: logging.LogRecord) -> None:
        """Clear context fields on a log record (for tests)."""
        record.job_id = record.model_id = record.session_id = "-"
        record.context = ""


def configure_logging_with_context(log_file_path=None, log_level="DEBUG"):
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper()))
    root.handlers.clear()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s%(context)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, log_level.upper()))
    ch.setFormatter(formatter)
    ch.addFilter(ContextFilter())
    root.addHandler(ch)

    fh = None
    if log_file_path:
        lp = Path(log_file_path)
        lp.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(lp, encoding="utf-8")
        fh.setLevel(getattr(logging, log_level.upper()))
        fh.setFormatter(formatter)
        fh.addFilter(ContextFilter())
        root.addHandler(fh)

    if log_level.upper() == "DEBUG" or (
        Path(log_file_path).name if log_file_path else ""
    ):  # simplified
        apply_per_logger_levels_for_verbose_root(log_level)
    return fh


def apply_per_logger_levels_for_verbose_root(_level):
    for n in _NOISY_WARNING_NAMES + _CHATBOT_FORMS_WARNING_NAMES:
        logging.getLogger(n).setLevel(logging.WARNING)
    for n in _PIPELINE_DIAG_INFO_NAMES:
        logging.getLogger(n).setLevel(logging.INFO)


async def generate_audit_trail_for_job(job_id: str) -> dict[str, Any]:
    job_db = get_job_db()
    job = await job_db.get_job_by_uid(job_id)
    if not job:
        return {"error": f"Job {job_id} not found"}

    job_dict = job.model_dump() if hasattr(job, "model_dump") else job
    related_messages = []
    try:
        chat_db = get_chat_history_db()
        convs = await chat_db.get_all_conversations()
        for c in convs:
            msgs = await chat_db.get_messages(c.conversation_id)
            for m in msgs:
                if m.tool_call_endpoint == job_dict.get("endpoint"):
                    related_messages.append(
                        {
                            "conversation_id": c.conversation_id,
                            "role": m.role,
                            "content": m.content,
                            "timestamp": m.timestamp,
                        }
                    )
    except UI_RENDER_ERRORS:
        pass

    audit = {
        "job_id": job_id,
        "generated_at": datetime.now().isoformat(),
        "job": job_dict,
        "related_chat_messages": related_messages,
    }
    try:
        audit["logs"] = await read_logs_filtered(job_id=job_id)
    except UI_RENDER_ERRORS:
        audit["logs"] = []
    return audit


async def read_logs_filtered(
    log_file_path=None,
    job_id=None,
    _model_id=None,
    _session_id=None,
    start_time=None,
    _end_time=None,
):
    path = Path(log_file_path or LOG_FILE)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        parsed = [p for p in (parse_log_line(line) for line in lines) if p]
        return [
            e
            for e in parsed
            if (not job_id or e.get("job_id") == job_id)
            and (
                not start_time or not e.get("timestamp") or e["timestamp"] >= start_time
            )
        ]
    except UI_RENDER_ERRORS:
        return []


def parse_log_line(line):
    pattern = (
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s*\| (.*?) \| (\S+) \| (.+)"
    )
    match = re.match(pattern, line)
    if not match:
        return None
    ts_str, level, ctx_str, _logger_name, message = match.groups()
    try:
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except UI_RENDER_ERRORS:
        ts = None
    jid = re.search(r"job_id=([^\s|]+)", ctx_str)
    return {
        "timestamp": ts,
        "level": level,
        "job_id": jid.group(1) if jid else None,
        "message": message,
    }


def format_audit_trail_markdown(audit_trail: dict[str, Any]) -> str:
    lines = [
        "# RescueBox Audit Trail",
        "",
        f"**Generated:** {audit_trail.get('generated_at')}",
        "",
        "## Job Information",
        "",
    ]
    job = audit_trail.get("job", {})
    lines.append(f"- **Job ID:** `{audit_trail.get('job_id')}`")
    lines.append(f"- **Status:** {job.get('status')}")
    return "\n".join(lines)


def parse_log_level(level_str: str) -> int:
    """Convert string log level to logging constant."""
    if not level_str:
        return logging.INFO
    return getattr(logging, level_str.upper(), logging.INFO)
