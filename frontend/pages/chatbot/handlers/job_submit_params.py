"""Positional job submission parameters for the chatbot orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class JobSubmitParams:
    request_body: Any
    endpoint: str
    task_schema: Any
    container: Any
    core: Any
    remaining_calls: Optional[list] = None
    conversation_id: Optional[str] = None
