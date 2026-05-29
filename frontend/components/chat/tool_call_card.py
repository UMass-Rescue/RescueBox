import json
import logging
from nicegui import ui
from typing import Any, Callable, Dict, Optional

from frontend.chatbot.config import ToolRegistry
from frontend.components.chat.message_card import ASSISTANT_PLAIN_CLASSES
from frontend.design_tokens import Design

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def format_tool_arguments_for_display(arguments: Any) -> str:
    """
    Pretty-print tool call arguments for chat UI (indented JSON-style, human-readable).
    """
    if arguments is None:
        return ""
    if isinstance(arguments, str):
        s = arguments.strip()
        if not s:
            return ""
        try:
            parsed = json.loads(s)
            return json.dumps(parsed, indent=2, ensure_ascii=False, default=str)
        except (json.JSONDecodeError, TypeError, ValueError):
            return arguments
    if isinstance(arguments, (dict, list, tuple)):
        try:
            return json.dumps(arguments, indent=2, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return str(arguments)
    return str(arguments)


def render_tool_call_card(
    container: ui.element,
    endpoint: str,
    arguments: Optional[Dict[str, Any]] = None,
    result_content: Optional[str] = None,
    on_rerun_tool: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ui_styling=None,
) -> None:
    """
    Render a tool call card with arguments, optional result, and re-run button.
    """
    try:
        endpoint_name = ToolRegistry.display_name_for_endpoint(endpoint)
        with container:
            with ui.row().classes("w-full flex justify-start"):
                # Quasar flat cards often swallow subtle rings; use an explicit border here.
                with ui.card().classes(
                    f"{Design.CHAT_ASSISTANT_BUBBLE} {Design.CHAT_ASSISTANT_BUBBLE_WIDTH} "
                    "!bg-white !ring-0 !border !border-solid !border-zinc-200 my-2"
                ).props("flat"):
                    ui.label(f"Plugin Selected · {endpoint_name}").classes(ASSISTANT_PLAIN_CLASSES)

                    if arguments:
                        _args_text = format_tool_arguments_for_display(arguments)
                        if _args_text:
                            ui.label("Arguments").classes(
                                f"{ASSISTANT_PLAIN_CLASSES} font-medium text-zinc-600"
                            )
                            ui.label(_args_text).classes(
                                f"{ASSISTANT_PLAIN_CLASSES} break-words min-w-0 whitespace-pre-line "
                                "font-mono text-sm text-zinc-800"
                            )

                    if on_rerun_tool:
                        async def _rerun():
                            logger.debug(
                                "tool_call_card: Re-run clicked for endpoint=%s arguments=%r",
                                endpoint,
                                arguments,
                            )
                            await on_rerun_tool(endpoint, arguments or {})

                        ui.button("Re-run Model", on_click=_rerun).classes(
                            getattr(
                                ui_styling,
                                "BUTTON_RERUN_TOOL",
                                "rb-brand-primary text-white",
                            )
                        )
    except Exception as e:
        logger.exception("Error rendering tool call card: %s", e)
