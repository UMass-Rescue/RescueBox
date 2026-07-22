import logging
from pathlib import Path

from nicegui import ui

from frontend.design_tokens import Design
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def read_log_file(log_file_path: Path, max_lines: int = 1000) -> str:
    """Read and process log file contents."""
    try:
        if not log_file_path.exists():
            return f"Log file does not exist: {log_file_path}"

        logger.info("Reading log file: %s", log_file_path)

        with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        if len(lines) > max_lines:
            lines = lines[-max_lines:]
            content = f"[Showing last {max_lines} lines of {len(lines) + (len(lines) - max_lines)} total lines]\n\n"
        else:
            content = ""

        content += "".join(lines)
        return content

    except UI_RENDER_ERRORS as e:
        error_msg = f"Error reading log file: {str(e)}"
        logger.error(error_msg)
        return error_msg


def render_log_viewer(
    container: ui.element,
    log_file: Path | None = None,
    max_lines: int = 1000,
    *,
    log_files: dict[str, Path] | None = None,
):
    """
    Render a log viewer inside `container` with search/filtering capabilities.
    Returns the code element for updates.
    """
    if log_files is None:
        if log_file is None:
            raise ValueError("render_log_viewer requires log_file or log_files")
        log_files = {"Log": log_file}

    def _selected_path() -> Path:
        name = source_select.value if source_select is not None else source_names[0]
        return log_files[name]

    source_names = list(log_files.keys())
    source_select: ui.select | None = None

    try:
        with container:
            # Controls row with Refresh and Search Input (instant typing filter)
            with ui.row().classes(
                "gap-4 items-center mb-4 w-full flex-wrap sm:flex-nowrap"
            ):
                if len(log_files) > 1:
                    source_select = (
                        ui.select(source_names, value=source_names[0], label="Log")
                        .props("outlined dense")
                        .classes("w-40 bg-white")
                    )

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

            path_label = ui.label("").classes(
                "text-sm text-zinc-600 w-full break-all font-mono mb-2"
            )

            # Log content display - full width, fill viewport height below navbar
            with ui.card().classes("w-full max-w-full min-w-0"):
                with ui.scroll_area().classes(
                    "min-h-[calc(100vh-12rem)] w-full max-w-full"
                ):
                    # Lightweight label (not ui.code) to avoid Prism.js lag on large logs
                    class LogDisplayLabel(ui.label):
                        @property
                        def content(self) -> str:
                            return self.text

                        @content.setter
                        def content(self, value: str):
                            self.set_text(value)

                        def refresh_text(self, value: str) -> None:
                            self.set_text(value)

                    log_display_cls = (
                        "w-full max-w-full text-xs font-mono whitespace-pre-wrap block "
                        "p-4 bg-slate-50 rounded-xl border border-slate-200 shadow-inner"
                    )
                    log_display = LogDisplayLabel().classes(log_display_cls)

            # Initialize attributes on log_display
            log_display.search_input = search_input
            log_display.raw_content = ""
            log_display.current_log_file = _selected_path()

            def _update_path_label() -> None:
                path = str(_selected_path())
                path_label.text = f"Log file: {path}"

            _update_path_label()

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
                    log_display.current_log_file = _selected_path()
                    _update_path_label()
                    content = read_log_file(log_display.current_log_file, max_lines)
                    log_display.raw_content = content
                    _apply_filter(search_input.value)
                except UI_RENDER_ERRORS as e:
                    logger.exception("Failed refreshing logs: %s", e)

            # Bind event handlers
            refresh_btn.on("click", lambda e=None: _refresh())
            search_input.on_value_change(lambda e: _apply_filter(e.value))
            if source_select is not None:
                source_select.on_value_change(lambda e=None: _refresh())

            # Return the element for callers to update
            return log_display
    except UI_RENDER_ERRORS as e:
        logger.exception("Failed to render log viewer: %s", e)
        with container:
            ui.label(f"Error rendering log viewer: {e}").classes("text-red-600")
        return None
