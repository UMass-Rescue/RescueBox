"""Chat message and persisted history rendering."""

from __future__ import annotations

import json
import logging
from typing import Any

from nicegui import ui

from frontend.chatbot.config import ToolRegistry
from frontend.components.chat import rerun_tool_call
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.design_tokens import Design
from frontend.pages.chatbot.state import ChatMessage

logger = logging.getLogger(__name__)


def _styled_chat_message(
    text: str,
    *,
    name: str,
    quasar_colors: tuple[str, str],
    sent: bool = False,
) -> ui.element:
    """Chat bubble colors via Quasar props (NiceGUI 3+ has no bg_color constructor args)."""
    background, foreground = quasar_colors
    msg = ui.chat_message(text, name=name, sent=sent)
    msg.props(f"bg-color={background} text-color={foreground}")
    return msg


def render_message(container: ui.element, message: ChatMessage):
    """Render a message in the chat container."""
    with container:
        if message.role == "user":
            _styled_chat_message(
                message.content,
                name="You",
                sent=True,
                quasar_colors=("blue-grey-1", "dark"),
            )
        else:
            _styled_chat_message(
                message.content,
                name="RescueBox Assistant",
                quasar_colors=("primary", "white"),
            )


def _history_record_to_chat_message(msg: Any) -> ChatMessage:
    """Map DB ``ChatMessageRecord`` to in-memory :class:`ChatMessage` (preserve type & payload)."""
    meta: dict[str, Any] = {}
    raw = getattr(msg, "metadata", None)
    if isinstance(raw, dict):
        meta.update(raw)
    if getattr(msg, "tool_call_endpoint", None):
        meta["tool_call_endpoint"] = msg.tool_call_endpoint
    ta = getattr(msg, "tool_call_arguments", None)
    if ta is not None:
        meta["tool_call_arguments"] = ta
    tcs = getattr(msg, "tool_calls", None)
    if tcs:
        meta["tool_calls"] = tcs
    return ChatMessage(
        role=getattr(msg, "role", "assistant"),
        content=getattr(msg, "content", "") or "",
        id=getattr(msg, "message_id", None),
        metadata=meta or None,
        message_type=getattr(msg, "message_type", "text") or "text",
    )


def _is_adjacent_job_started_then_completed(started: Any, completed: Any) -> bool:
    """True when DB has back-to-back tool_result rows for the same job (run → done)."""
    if getattr(started, "message_type", "") != "tool_result":
        return False
    if getattr(completed, "message_type", "") != "tool_result":
        return False
    js = (getattr(started, "metadata", None) or {}).get("job_id")
    jc = (getattr(completed, "metadata", None) or {}).get("job_id")
    if not js or js != jc:
        return False
    sa = (getattr(started, "metadata", None) or {}).get("status", "")
    sc = (getattr(completed, "metadata", None) or {}).get("status", "")
    if str(sa).upper() == "RUNNING" and str(sc).lower() == "completed":
        return True
    ta = (getattr(started, "content", "") or "").lower()
    tb = (getattr(completed, "content", "") or "").lower()
    if "started" in ta and ("completed" in tb or "successfully" in tb):
        return True
    return False


def render_merged_job_tool_results(
    container: ui.element, started_msg: Any, completed_msg: Any
) -> None:
    """
    Single card for a job lifecycle row pair: no duplicate job-details buttons.

    Uses ``started_msg`` for inputs/parameters (only the start row stores the snapshot).
    """
    with container, ui.card().classes(
        "w-full max-w-3xl border border-slate-200 rounded-2xl p-5 bg-slate-50 "
        "shadow-sm space-y-2 border-l-4 border-l-[#881c1c]"
    ):
        ui.label("Assistant").classes(
            "text-sm font-semibold text-slate-500 uppercase tracking-wider"
        )
        ui.label((getattr(started_msg, "content", "") or "").strip()).classes(
            "text-base text-slate-800 whitespace-pre-wrap break-words font-medium"
        )
        ui.label((getattr(completed_msg, "content", "") or "").strip()).classes(
            "text-base text-emerald-700 font-semibold whitespace-pre-wrap break-words"
        )
        ep = getattr(started_msg, "tool_call_endpoint", None)
        if ep:
            try:
                dn = ToolRegistry.display_name_for_endpoint(ep)
            except UI_RENDER_ERRORS:
                dn = ep
            ui.label(f"Plugin: {dn}").classes("text-sm text-slate-500")
        args = getattr(started_msg, "tool_call_arguments", None)
        if isinstance(args, dict) and (
            args.get("inputs") is not None or args.get("parameters") is not None
        ):
            with ui.expansion("Job inputs & parameters", value=False).classes("w-full"):
                ui.code(json.dumps(args, indent=2, default=str)).classes(
                    "text-xs w-full whitespace-pre-wrap break-all"
                )
        meta = getattr(started_msg, "metadata", None) or {}
        jid = meta.get("job_id") if isinstance(meta, dict) else None
        if jid:

            def _open_job() -> None:
                ui.navigate.to(f"/jobs/{jid}")

            ui.button(
                "Open job details",
                color=None,
                on_click=_open_job,
            ).classes(f"mt-1 {Design.BTN_MEDIUM_GRAY}")
        _append_rerun_job_button(started_msg)


def _append_rerun_job_button(msg: Any) -> None:
    """Re-run using the persisted message id (tool_call or tool_result with job snapshot)."""
    message_id = getattr(msg, "message_id", None)
    if not message_id:
        return

    async def _do_rerun(_event=None) -> None:
        await rerun_tool_call(message_id)

    ui.button("Re-run Job", icon="replay", on_click=_do_rerun).classes(
        f"mt-1 {Design.BTN_MEDIUM_GRAY}"
    )


def render_persisted_history_message(container: ui.element, msg: Any) -> None:
    """
    Render one persisted row in the main chat (matches v3_demo rich history: job payload, tool calls).

    Plain :func:`render_message` only sees role+text, so loaded chats would lose
    ``tool_call_arguments`` (saved job inputs) and message type.
    """
    mt = getattr(msg, "message_type", None) or "text"
    role = getattr(msg, "role", "assistant")
    content = (getattr(msg, "content", None) or "").strip()

    if mt == "tool_result":
        with container, ui.card().classes(
            "w-full max-w-3xl border border-slate-200 rounded-2xl p-5 bg-slate-50 "
            "shadow-sm space-y-2 border-l-4 border-l-[#881c1c]"
        ):
            ui.label("Assistant").classes(
                "text-sm font-semibold text-slate-500 uppercase tracking-wider"
            )
            ui.label(content).classes(
                "text-base text-slate-800 whitespace-pre-wrap break-words font-medium"
            )
            ep = getattr(msg, "tool_call_endpoint", None)
            if ep:
                try:
                    dn = ToolRegistry.display_name_for_endpoint(ep)
                except UI_RENDER_ERRORS:
                    dn = ep
                ui.label(f"Plugin: {dn}").classes("text-sm text-slate-500")
            args = getattr(msg, "tool_call_arguments", None)
            if isinstance(args, dict) and (
                args.get("inputs") is not None or args.get("parameters") is not None
            ):
                with ui.expansion("Job inputs & parameters", value=False).classes(
                    "w-full"
                ):
                    ui.code(json.dumps(args, indent=2, default=str)).classes(
                        "text-xs w-full whitespace-pre-wrap break-all"
                    )
            meta = getattr(msg, "metadata", None) or {}
            if isinstance(meta, dict) and meta.get("job_id"):
                jid = meta["job_id"]

                def _open_job() -> None:
                    ui.navigate.to(f"/jobs/{jid}")

                ui.button(
                    "Open job details",
                    color=None,
                    on_click=_open_job,
                ).classes(f"mt-1 {Design.BTN_MEDIUM_GRAY}")
            _append_rerun_job_button(msg)

    if mt == "tool_call":
        with container, ui.card().classes(
            "w-full max-w-3xl border border-slate-200 rounded-2xl p-5 "
            "bg-amber-50/80 space-y-2 border-l-4 border-l-[#881c1c]"
        ):
            ui.label("Tool call").classes(
                "text-sm font-semibold text-[#881c1c] uppercase tracking-wider"
            )
            tcalls = getattr(msg, "tool_calls", None) or []
            if tcalls:
                ui.code(json.dumps(tcalls, indent=2, default=str)).classes(
                    "text-xs w-full whitespace-pre-wrap"
                )
            elif content:
                ui.label(content).classes("text-base text-slate-800")
            _append_rerun_job_button(msg)
    if mt == "error":
        with container, ui.card().classes(
            "w-full max-w-3xl border border-red-200 bg-red-50 p-4 space-y-1"
        ):
            ui.label("Error").classes("text-sm font-semibold text-red-800")
            ui.label(content).classes("text-base text-red-900 whitespace-pre-wrap")
        return

    with container:
        if role == "user":
            _styled_chat_message(
                content,
                name="You",
                sent=True,
                quasar_colors=("blue-grey-1", "dark"),
            )
        else:
            _styled_chat_message(
                content,
                name="RescueBox Assistant",
                quasar_colors=("primary", "white"),
            )
