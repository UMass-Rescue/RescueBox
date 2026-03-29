"""
Logging Context Manager

This module provides contextual logging with session ID, job ID, and model ID
tracking. All log messages will include these identifiers when available.

Usage:
    from frontend.utils.logging_context import set_logging_context, get_logging_context
    
    # Set context for a job
    set_logging_context(job_id='job_123', model_id='model_456', session_id='session_789')
    
    # Log messages will automatically include these IDs
    logger.info("Processing job")
    
    # Get current context
    context = get_logging_context()

Features:
Contextual logging: All log messages include job_id, model_id, and session_id when set

Log filtering: Audit trail includes only logs matching the job's IDs

Time-based filtering: Only includes logs within the job's execution window

Structured format: Logs are in a parseable format for easy filtering

How It Works:

On application start: Logging is configured with the context filter
On job creation: Logging context is set with job_id, model_id, and session_id
During execution: All log messages include these IDs

On audit trail generation:
Reads the log file
Filters entries matching the job's job_id and model_id
Filters by time range (job start to end time)
Includes matching logs in the exported audit trail

Example Log Format:
2024-01-15 10:30:45 | INFO     | job_id=abc123 | model_id=model456 | session_id=session789 | frontend.pages.chatbot.chatbot_handlers | Job abc123 created in database


"""

import logging
import contextvars
import os
from typing import Optional, Dict, Any
from datetime import datetime


# Context variables for tracking IDs
_job_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('job_id', default=None)
_model_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('model_id', default=None)
_session_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('session_id', default=None)


def set_logging_context(
    job_id: Optional[str] = None,
    model_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """
    Set logging context for current execution context.
    
    Args:
        job_id: Job unique identifier
        model_id: Model unique identifier
        session_id: Session/conversation unique identifier
    
    Tips:
    - Context is thread-safe and async-safe (using contextvars)
    - Context persists for the duration of the execution context
    - Can be set at any point during execution
    - Overwrites previous values if provided
    """
    if job_id is not None:
        _job_id.set(job_id)
    if model_id is not None:
        _model_id.set(model_id)
    if session_id is not None:
        _session_id.set(session_id)


def get_logging_context() -> Dict[str, Optional[str]]:
    """
    Get current logging context.
    
    Returns:
        Dict with job_id, model_id, and session_id (may be None)
    """
    return {
        'job_id': _job_id.get(None),
        'model_id': _model_id.get(None),
        'session_id': _session_id.get(None)
    }


def clear_logging_context():
    """
    Clear all logging context.
    
    Resets job_id, model_id, and session_id to None.
    """
    _job_id.set(None)
    _model_id.set(None)
    _session_id.set(None)


class ContextFilter(logging.Filter):
    """
    Logging filter that adds contextual information (job_id, model_id, session_id) to log records.
    
    This filter extracts context from contextvars and adds it as extra fields to log records.
    The formatted log message will include these IDs in a structured format.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add contextual information to log record.
        
        Args:
            record: Log record to modify
        
        Returns:
            bool: Always True (doesn't filter out any records)
        """
        try:
            job_id = _job_id.get(None)
            model_id = _model_id.get(None)
            session_id = _session_id.get(None)
            
            # Add to record as extra fields
            record.job_id = job_id or '-'
            record.model_id = model_id or '-'
            record.session_id = session_id or '-'
            
            # Create context string for log formatting
            context_parts = []
            if job_id:
                context_parts.append(f"job_id={job_id}")
            if model_id:
                context_parts.append(f"model_id={model_id}")
            if session_id:
                context_parts.append(f"session_id={session_id}")

            # Format: " | job_id=abc | model_id=def | session_id=ghi" or ""
            record.context = f" | {' | '.join(context_parts)}" if context_parts else ""
            
        except Exception:
            # If contextvars fail, set defaults
            record.job_id = '-'
            record.model_id = '-'
            record.session_id = '-'
            record.context = ""
        
        return True


def configure_logging_with_context(log_file_path: Optional[str] = None, log_level: str = 'DEBUG'):
    """
    Configure logging with context filter and file handler.
    
    Args:
        log_file_path: Path to log file (if None, logs only to console)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Handler: File handler if log_file_path provided, else None
    
    Tips:
    - Adds ContextFilter to root logger
    - Configures format to include contextual IDs
    - Creates file handler if log_file_path provided
    - Format: timestamp | level | job_id | model_id | session_id | logger | message
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create formatter that includes context only when available
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s%(context)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    console_handler.addFilter(ContextFilter())
    root_logger.addHandler(console_handler)
    
    # File handler (if path provided)
    file_handler = None
    if log_file_path:
        from pathlib import Path
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        file_handler.addFilter(ContextFilter())
        root_logger.addHandler(file_handler)
    
    # Ensure handler levels respect DEBUG when requested either via parameter or environment
    try:
        env_level = os.getenv('LOG_LEVEL', '').upper()
    except Exception:
        env_level = ''

    if log_level.upper() == 'DEBUG' or env_level == 'DEBUG':
        root_logger.setLevel(logging.DEBUG)
        for h in root_logger.handlers:
            try:
                h.setLevel(logging.DEBUG)
            except Exception:
                pass

        # Also ensure existing module loggers do not block DEBUG by resetting their level to NOTSET.
        try:
            mgr = getattr(logging, 'manager', None) or getattr(logging.getLogger(), 'manager', None)
            if mgr is not None and hasattr(mgr, 'loggerDict'):
                for name, logger_obj in list(mgr.loggerDict.items()):
                    # loggerObj can be a PlaceHolder in some setups; ensure it's Logger
                    if isinstance(logger_obj, logging.Logger):
                        try:
                            logger_obj.setLevel(logging.NOTSET)
                        except Exception:
                            pass
            for noisy in (
                'socketio.server',
                'socketio',
                'engineio.server',
                'engineio',
                # FUSE / python-fuse: getattr/getxattr DEBUG noise on UFDR mounts
                'fuse',
                'fuse.log-mixin',
                'ufdr_mounter.utils.ufdr_mount_unix',
                # Chatbot page load / conversation init (verbose INFO+DEBUG)
                'frontend.pages.chatbot',
                'frontend.database.chat_history_db',
                'frontend.utils.nicegui_storage',
                # HTTP client stack (httpx/httpcore DEBUG)
                'httpcore',
                'httpcore.http11',
                'httpx',
                # Chatbot package (schema_utils, utils) — not under pages.chatbot
                'frontend.chatbot',
                # Forms / validators / file browser (normal-path INFO+DEBUG)
                'frontend.components.forms',
                'frontend.components.results.tool_selection_card',
                'frontend.utils.validators',
                'frontend.utils.file_browser',
                'nicegui',
                # Per-module logger.setLevel(DEBUG) overrides parents — force quiet explicitly
                'frontend.pages.chatbot.chatbot_forms',
                'frontend.pages.chatbot.chatbot',
                'frontend.pages.chatbot.state.state_manager',
                'frontend.pages.chatbot.utils.form_validator',
                'frontend.components.forms.form_generator',
                'frontend.components.forms.form_handlers',
                'frontend.components.forms.builders.input_field_builder',
                'frontend.components.forms.case_notes_dialog',
            ):
                logging.getLogger(noisy).setLevel(logging.WARNING)
        except Exception:
            # best-effort; don't fail logging setup if introspection fails
            pass

    return file_handler

