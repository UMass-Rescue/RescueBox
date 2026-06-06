import logging
from pathlib import Path
from nicegui import ui
from frontend.design_tokens import Design

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_log_viewer(container: ui.element, log_file: Path, max_lines: int = 1000):
    """
    Render a log viewer inside `container` with search/filtering capabilities.
    Returns the code element for updates.
    """
    try:
        with container:
            # Controls row with Refresh and Search Input (instant typing filter)
            with ui.row().classes(
                "gap-4 items-center mb-4 w-full flex-wrap sm:flex-nowrap"
            ):
                refresh_btn = (
                    ui.button("Refresh")
                    .props("icon=refresh")
                    .classes(Design.BTN_PRIMARY_COMPACT)
                )

                # Search input with prepended search icon, clearable prop, and debounce
                search_input = (
                    ui.input(
                        placeholder="Search/filter logs...",
                    )
                    .props("outlined dense clearable debounce=300")
                    .classes("w-64 bg-white")
                )
                with search_input.add_slot("prepend"):
                    ui.icon("search").classes("text-slate-400")

                ui.label(f"Log file: {str(log_file)}").classes("text-sm text-zinc-600")

            # Log content display - full width, fill viewport height below navbar
            with ui.card().classes("w-full max-w-full min-w-0"):
                with ui.scroll_area().classes(
                    "min-h-[calc(100vh-12rem)] w-full max-w-full"
                ):
                    # Use a custom lightweight label subclass instead of ui.code to prevent Prism.js DOM bloat and focus lag
                    class LogDisplayLabel(ui.label):
                        @property
                        def content(self) -> str:
                            return self.text

                        @content.setter
                        def content(self, value: str):
                            self.set_text(value)

                    log_display = LogDisplayLabel().classes(
                        "w-full max-w-full text-xs font-mono whitespace-pre-wrap block p-4 bg-slate-50 rounded-xl border border-slate-200 shadow-inner"
                    )

            # Initialize attributes on log_display
            log_display.search_input = search_input
            log_display.raw_content = ""

            def _apply_filter(query: str = None):
                if query is None:
                    query = (search_input.value or "").strip()
                else:
                    query = str(query).strip() if query is not None else ""

                if not log_display.raw_content:
                    log_display.content = ""
                    return

                if not query:
                    log_display.content = log_display.raw_content
                    return

                # Filter lines
                lines = log_display.raw_content.splitlines()
                matching_lines = [
                    line for line in lines if query.lower() in line.lower()
                ]

                if matching_lines:
                    header = f"[Found {len(matching_lines)} matching lines for '{query}']\n\n"
                    log_display.content = header + "\n".join(matching_lines)
                else:
                    log_display.content = f"[No matching lines found for '{query}']"

            # Expose apply_filter on log_display so external callers can trigger it
            log_display.apply_filter = _apply_filter

            # Attach simple refresh handler
            def _refresh():
                try:
                    from frontend.pages.logs import read_log_file

                    content = read_log_file(log_file, max_lines)
                    log_display.raw_content = content
                    _apply_filter(search_input.value)
                except Exception as e:
                    logger.exception("Failed refreshing logs: %s", e)

            # Bind event handlers
            refresh_btn.on("click", lambda e=None: _refresh())
            search_input.on_value_change(lambda e: _apply_filter(e.value))

            # Return the element for callers to update
            return log_display
    except Exception as e:
        logger.exception("Failed to render log viewer: %s", e)
        with container:
            ui.label(f"Error rendering log viewer: {e}").classes("text-red-600")
        return None
