"""
Typed bundles for chat UI flows (reduces long parameter lists).

New code should prefer these dataclasses; legacy call sites may keep keyword args
until migrated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass
class MessageSendParams:
    """Arguments for :meth:`MessageSender.send_message_params`."""

    message_text: str
    input_field: Any
    is_processing_ref: Dict[str, Any]
    message_handler: Any
    process_handler_result_func: Callable[..., Any]
    add_message_func: Callable[..., Any]
    show_error_func: Callable[..., Any]
    update_status_func: Callable[..., Any]
    conversation_id_ref: Optional[Dict[str, Any]] = None
