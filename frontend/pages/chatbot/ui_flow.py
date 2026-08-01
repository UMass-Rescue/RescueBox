"""Chatbot UI helpers shared by the page and coordinator (no coordinator import)."""

from __future__ import annotations

import logging

from nicegui import ui

from frontend.chatbot.pipeline_context import inject_pipeline_path
from frontend.components.errors import render_error_message
from frontend.components.results import render_tool_selection_message
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.pages.chatbot.pickers import AnalysisPicker, ToolPicker
from frontend.pages.chatbot.storage_reads import read_pipeline_job_id
from frontend.utils import handle_api_error

logger = logging.getLogger(__name__)

element = ui.element
label = ui.label
card = ui.card
button = ui.button
navigate = ui.navigate


def show_error_message(container: element, message: str):
    """Show an error message in the chat container."""
    render_error_message(container, message)


async def show_tool_picker(container: ui.element, tool_registry, on_tool_selected):
    picker = ToolPicker(container, tool_registry, on_tool_selected)
    await picker.show()


async def show_analysis_picker(container: ui.element, on_analysis_selected):
    picker = AnalysisPicker(container, on_analysis_selected)
    await picker.show()


async def show_tool_selection(container: element, endpoint: str):
    try:
        render_tool_selection_message(container, endpoint)
    except UI_RENDER_ERRORS:
        with container:
            label(f"Running {endpoint}...").classes("text-sm text-slate-500 italic")


async def load_and_show_form(
    container, core, endpoint, arguments, on_form_submit, on_form_cancel=None
):
    try:
        task_schema = await core.get_task_schema_from_endpoint(endpoint)
        if not task_schema:
            await handle_api_error(
                ValueError(f"Could not load tool configuration for {endpoint}"),
                "Form loading",
            )
            return

        pipeline_job_id = read_pipeline_job_id()
        arguments = inject_pipeline_path(arguments, task_schema, pipeline_job_id)

        initial_values = core.convert_arguments_to_initial_values(
            arguments, task_schema, endpoint
        )

        async def _wrapped_submit(form_data, endpoint=None, task_schema=None, **kwargs):
            return await on_form_submit(
                form_data, endpoint=endpoint, task_schema=task_schema, **kwargs
            )

        return await core.create_input_form(
            task_schema,
            endpoint,
            initial_values=initial_values,
            on_submit=_wrapped_submit,
            on_cancel=on_form_cancel,
            container=container,
        )
    except UI_RENDER_ERRORS as e:
        logger.exception("Error in load_and_show_form: %s", e)
        await handle_api_error(e, "Form loading")
        show_error_message(container, f"Failed to load form: {e!s}")


async def show_results(
    container: element, response_body, job_id: str | None = None, **kwargs
):
    """Compact job-completed strip with link to full results."""
    try:
        with container:
            await _show_results_body(container, response_body, job_id, **kwargs)
    except UI_RENDER_ERRORS as e:
        logger.error("Error showing results: %s", e)
        await handle_api_error(e, "Results rendering")


async def _show_results_body(
    container: element, _response_body, job_id: str | None, **_kwargs
) -> None:
    with container:
        with card().classes(
            "rb-job-result-anchor w-full max-w-md rounded-xl border-2 border-green-400 "
            "bg-gradient-to-br from-green-50 to-emerald-50 p-4 shadow-sm flex flex-col gap-3"
        ):
            label("Job completed").classes("text-base font-semibold text-green-900")

            if job_id:

                def _open_results() -> None:
                    navigate.to(f"/jobs/{job_id}")

                button(
                    "View results",
                    on_click=_open_results,
                ).classes(
                    "w-full bg-green-600 hover:bg-green-700 text-white "
                    "font-medium py-3 rounded-lg shadow-sm"
                )
