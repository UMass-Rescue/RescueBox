import logging
from nicegui import ui
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def render_tool_call_card(container: ui.element,
                          endpoint: str,
                          arguments: Optional[Dict[str, Any]] = None,
                          result_content: Optional[str] = None,
                          on_rerun_tool: Optional[Callable[[str, Dict[str, Any]], None]] = None,
                          ui_styling=None) -> None:
    """
    Render a tool call card with arguments, optional result, and re-run button.
    """
    try:
        with container:
            with ui.card().classes(
                getattr(ui_styling, "CARD_TOOL_CALL", "p-4 my-2 bg-zinc-50 border border-zinc-200 rounded-lg")
            ):
                ui.label(f"Plugin · {endpoint}").classes(
                    getattr(ui_styling, 'LABEL_TOOL_CALL_TITLE', 'font-semibold')
                )

                if arguments:
                    ui.label(f"Arguments: {arguments}").classes(getattr(ui_styling, 'LABEL_TOOL_CALL_ARGS', 'text-sm'))

                #if result_content:
                #    ui.label('Result').classes(getattr(ui_styling, 'LABEL_TOOL_RESULT_TITLE', 'font-semibold mt-2'))
                #    ui.label(result_content).classes(getattr(ui_styling, 'LABEL_TOOL_RESULT_CONTENT', 'text-sm'))

                if on_rerun_tool:
                    async def _rerun():
                        logger.debug("tool_call_card: Re-run clicked for endpoint=%s arguments=%r", endpoint, arguments)
                        await on_rerun_tool(endpoint, arguments or {})
                    ui.button('Re-run Model', on_click=_rerun).classes(getattr(ui_styling, 'BUTTON_RERUN_TOOL', 'rb-brand-primary text-white'))
    except Exception as e:
        logger.exception("Error rendering tool call card: %s", e)
