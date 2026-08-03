from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from nicegui import ui

from frontend.chatbot.multi_tool_handler import (
    apply_metadata_filter,
    batch_items_have_age_gender_metadata,
    chain_output_to_input,
    coerce_pipeline_response,
    extract_batch_file_items,
)
from frontend.components.chat import UIOperations
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.database import get_job_db
from frontend.design_tokens import Design
from frontend.pages.chatbot.handlers.job_submit_params import JobSubmitParams
from frontend.pages.chatbot.handlers.pipeline_planner import (
    inject_filtered_paths_into_request,
    plan_next_pipeline_step,
)
from frontend.pages.chatbot.ui_flow import load_and_show_form
from frontend.utils import notify_info, notify_warning

if TYPE_CHECKING:
    from .job_orchestrator import JobSubmissionOrchestrator

logger = logging.getLogger(__name__)


def compose_age_gender_pipeline_filter(gender, age_op, age_val):
    parts = []
    if gender:
        parts.append(f"Gender={gender}")
    if age_val is not None:
        sym = {"lt": "<", "lte": "<=", "eq": "=", "gt": ">", "gte": ">="}.get(
            age_op, "<"
        )
        parts.append(f"Age {sym} {age_val}")
    return ", ".join(parts)


class PipelineHandler:
    """Handles multi-step job submission workflows."""

    def __init__(self, orchestrator: JobSubmissionOrchestrator):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(__name__)

    def has_remaining(self, remaining_calls) -> bool:
        """True when there is at least one queued pipeline step."""
        return bool(remaining_calls)

    async def handle_remaining_calls(
        self,
        remaining_calls,
        response_body,
        container,
        core,
        _load_form_func=None,
        accumulated_endpoint_chain=None,
        pipeline_total_steps=None,
        pipeline_root_job_id=None,
        completed_step_job_id=None,
    ):
        if not remaining_calls:
            return
        try:
            next_call = remaining_calls[0]
            next_schema = await core.get_task_schema_from_endpoint(
                next_call["endpoint"]
            )
            plan = plan_next_pipeline_step(
                response_body,
                next_call,
                next_schema,
                coerce_response_fn=coerce_pipeline_response,
                chain_output_fn=chain_output_to_input,
                extract_items_fn=extract_batch_file_items,
                has_metadata_fn=batch_items_have_age_gender_metadata,
            )

            filtered_paths = None
            criteria = ""
            if plan.items:
                if plan.has_age_gender_metadata:
                    criteria = await self._show_filter_criteria_dialog(container)
                else:
                    criteria = ""
                filtered_paths = apply_metadata_filter(plan.items, criteria)
                if completed_step_job_id and plan.has_age_gender_metadata:
                    try:
                        jdb = get_job_db()
                        await jdb.update_job_pipeline_metadata_filter_criteria(
                            completed_step_job_id, criteria
                        )
                    except UI_RENDER_ERRORS:
                        pass

            def _on_cancel():
                if self.orchestrator.form_handler.state_manager:
                    self.orchestrator.form_handler.state_manager.set_input_enabled(True)

            with container:
                if plan.items and criteria and criteria.strip() and not filtered_paths:
                    notify_warning(
                        "No files matched your filter; the next step will process no images."
                    )
                if next_schema:
                    notify_info(f"Proceeding to next operation: {plan.next_endpoint}")

                await load_and_show_form(
                    container,
                    core,
                    plan.next_endpoint,
                    plan.next_arguments,
                    self._create_next_form_handler(
                        remaining_calls[1:] if len(remaining_calls) > 1 else None,
                        container,
                        core,
                        filtered_paths,
                        accumulated_endpoint_chain,
                        pipeline_total_steps,
                        pipeline_root_job_id,
                    ),
                    on_form_cancel=_on_cancel,
                )
                try:
                    await UIOperations.safe_container_update(container)
                except UI_RENDER_ERRORS:
                    pass
                UIOperations.scroll_form_into_view_with_retries(
                    client=getattr(container, "client", None)
                )
        except UI_RENDER_ERRORS as e:
            self.logger.error("Error handling remaining calls: %s", str(e))

    async def _show_filter_criteria_dialog(self, container) -> str:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[str] = loop.create_future()

        def _finish(value: str):
            if not future.done():
                future.set_result(value.strip())

        with container:
            with ui.dialog() as dialog, ui.card().classes("w-[400px]"):
                ui.label("Filter files before next step").classes(
                    "text-lg font-semibold"
                )
                gender_select = ui.select(
                    options={"": "Any gender", "male": "Male", "female": "Female"},
                    value="",
                    label="Gender",
                ).classes("w-full mt-2")
                with ui.row().classes("w-full items-end gap-2 flex-wrap"):
                    age_op_select = ui.select(
                        options={
                            "lt": "Less than",
                            "lte": "At most",
                            "eq": "Equals",
                            "gt": "Greater than",
                            "gte": "At least",
                        },
                        value="lt",
                        label="Compare",
                    ).classes("min-w-[9rem] flex-1")
                    age_number = ui.number(
                        label="Years", value=None, min=0, max=120, format="%.0f"
                    ).classes("min-w-[6rem] flex-1")

                def _use_all():
                    _finish("")
                    dialog.close()

                def _apply_filter():
                    raw = age_number.value
                    age_val = None
                    if raw is not None and raw != "":
                        try:
                            age_val = float(raw)
                        except UI_RENDER_ERRORS:
                            notify_warning(
                                "Enter a valid age number, or leave age empty."
                            )
                            return
                    crit = compose_age_gender_pipeline_filter(
                        str(gender_select.value or ""),
                        str(age_op_select.value or "lt"),
                        age_val,
                    )
                    _finish(crit.strip())
                    dialog.close()

                with ui.row().classes("mt-4 gap-2"):
                    ui.button("Use all", on_click=_use_all, color=None).classes(
                        Design.BTN_MEDIUM_GRAY
                    )
                    ui.button(
                        "Apply filter", on_click=_apply_filter, color=None
                    ).classes(Design.BTN_PRIMARY_COMPACT)
            dialog.open()
        try:
            return await asyncio.wait_for(future, timeout=120.0)
        except UI_RENDER_ERRORS:
            return ""

    def _create_next_form_handler(
        self,
        remaining_calls,
        container,
        core,
        filtered_paths=None,
        accumulated_endpoint_chain=None,
        pipeline_total_steps=None,
        pipeline_root_job_id=None,
    ):
        async def handle_next_form(
            request_body, endpoint=None, task_schema=None, **kwargs
        ):
            effective_endpoint = (
                endpoint or kwargs.get("next_endpoint") or kwargs.get("endpoint")
            )

            try:
                request_body = inject_filtered_paths_into_request(
                    request_body, filtered_paths
                )
            except UI_RENDER_ERRORS:
                pass
            conversation_id = (
                self.orchestrator.form_handler.state_manager.conversation_id
            )
            chain = list(accumulated_endpoint_chain or []) + [effective_endpoint]
            params = JobSubmitParams(
                request_body=request_body,
                endpoint=effective_endpoint,
                task_schema=task_schema,
                container=container,
                core=core,
                remaining_calls=remaining_calls,
                conversation_id=conversation_id,
            )
            await self.orchestrator.submit_job(
                params,
                endpoint_chain=chain,
                pipeline_total_steps=pipeline_total_steps,
                pipeline_root_job_id=pipeline_root_job_id,
            )

        return handle_next_form
