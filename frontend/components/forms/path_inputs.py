"""Path input components for selecting files and directories."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from nicegui import ui
from rb.api.models import DirectoryInput, FileInput

from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.design_tokens import Design
from frontend.utils import (
    browse_directory_simple,
    browse_file_simple,
    get_active_case,
    maybe_autofill_output_dir_field,
    maybe_autofill_ufdr_mount_name_field,
)

logger = logging.getLogger(__name__)


def create_directory_input(
    field_id: str,
    initial_value: Any,
    form_widgets: dict[str, Any],
    autofill_output_key: str | None = None,
) -> None:
    """Render a directory path input with validation icon and browse dialog."""
    active_case = get_active_case()
    case_path = active_case.evidencePath if active_case else ""

    val = ""
    if isinstance(initial_value, dict):
        val = str(initial_value.get("path", "") or "").strip()
    elif isinstance(initial_value, str):
        val = initial_value.strip()

    placeholder = case_path or "/path/to/directory"

    with ui.column().classes("w-full min-w-0 gap-1"):
        ui.label("Directory path").classes("text-sm font-medium text-zinc-700")
        with ui.row().classes("w-full min-w-0 items-center gap-2 flex-nowrap"):
            dir_input = (
                ui.input(
                    placeholder=placeholder,
                    value=val,
                )
                .classes("flex-1 min-w-0")
                .props("outlined dense clearable")
            )
            v_icon = ui.icon("").classes("text-zinc-400 shrink-0")

            def validate():
                p = dir_input.value.strip()
                if not p:
                    v_icon.name = ""
                    return
                try:
                    DirectoryInput(path=Path(p))
                    v_icon.name = "check_circle"
                    v_icon.classes(
                        "text-green-500", remove="text-red-500 text-zinc-400"
                    )
                    if autofill_output_key:
                        maybe_autofill_output_dir_field(
                            form_widgets, autofill_output_key, p
                        )
                except UI_RENDER_ERRORS:
                    v_icon.name = "error"
                    v_icon.classes(
                        "text-red-500", remove="text-green-500 text-zinc-400"
                    )

            def clear_path():
                dir_input.set_value("")
                validate()

            dir_input.on("change", validate)
            if val:
                validate()

            ui.button("Clear", on_click=clear_path).classes(
                f"{Design.BTN_MEDIUM_GRAY} shrink-0"
            )
            ui.button(
                "Browse",
                on_click=lambda: browse_directory_simple(
                    dir_input,
                    initial_path=dir_input.value.strip() or case_path or None,
                    on_after_select=validate,
                ),
            ).classes(f"{Design.BTN_MEDIUM_GRAY} shrink-0")
    form_widgets[field_id] = dir_input


def create_file_input(
    field_id: str,
    initial_value: Any,
    form_widgets: dict[str, Any],
    autofill_mount_key: str | None = None,
) -> None:
    """Render a file path input with validation icon and file browse dialog."""
    active_case = get_active_case()
    default_path = active_case.evidencePath if active_case else ""

    val = ""
    if isinstance(initial_value, dict):
        val = initial_value.get("path", "")
    elif isinstance(initial_value, str):
        val = initial_value

    with ui.column().classes("w-full min-w-0 gap-1"):
        ui.label("File path").classes("text-sm font-medium text-zinc-700")
        with ui.row().classes("w-full min-w-0 items-center gap-2 flex-nowrap"):
            file_input = (
                ui.input(
                    placeholder="/path/to/file",
                    value=val,
                )
                .classes("flex-1 min-w-0")
                .props("outlined dense")
            )
            v_icon = ui.icon("").classes("text-zinc-400 shrink-0")

            def validate():
                p = file_input.value.strip()
                if not p:
                    v_icon.name = ""
                    return
                try:
                    FileInput(path=Path(p))
                    v_icon.name = "check_circle"
                    v_icon.classes(
                        "text-green-500", remove="text-red-500 text-zinc-400"
                    )
                    if autofill_mount_key:
                        maybe_autofill_ufdr_mount_name_field(
                            form_widgets, autofill_mount_key, p
                        )
                except UI_RENDER_ERRORS:
                    v_icon.name = "error"
                    v_icon.classes(
                        "text-red-500", remove="text-green-500 text-zinc-400"
                    )

            file_input.on("change", validate)
            if file_input.value:
                validate()
            ui.button(
                "Browse",
                on_click=lambda: browse_file_simple(
                    file_input,
                    initial_path=default_path or None,
                    on_after_select=validate,
                ),
            ).classes(Design.BTN_MEDIUM_GRAY)
    form_widgets[field_id] = file_input
