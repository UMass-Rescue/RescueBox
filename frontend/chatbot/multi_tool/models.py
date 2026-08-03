"""Shared data models for chatbot multi-tool orchestration."""

from __future__ import annotations

from typing import Any

from rb.api.models import ResponseBody


class MultiToolCallResult:
    """Result container for executing multiple tool calls."""

    def __init__(self):
        self.tool_calls: list[dict[str, Any]] = []
        self.results: list[ResponseBody | None] = []
        self.errors: list[str | None] = []
        self.completed_count = 0

    def add_result(
        self,
        tool_call: dict[str, Any],
        result: ResponseBody | None,
        error: str | None = None,
    ) -> None:
        """Record one tool call outcome."""
        self.tool_calls.append(tool_call)
        self.results.append(result)
        self.errors.append(error)
        if result:
            self.completed_count += 1

    def result_count(self) -> int:
        """Number of tool calls that completed without error."""
        return self.completed_count
