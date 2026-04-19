"""
Job Details Page

This module provides the job details page for displaying job information,
outputs, inputs, and parameters with validation using Pydantic models.
"""

import logging
import sys
import httpx
from pathlib import Path

from nicegui import ui

# Add backend models to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from rb.api.models import TaskSchema, RequestBody, ResponseBody

from frontend.components.results import ResultsPreview
from frontend.components.shared import create_navbar
from frontend.components.shared.breadcrumbs import create_breadcrumbs
from frontend.database import get_job_db
from frontend.pages.jobs.job_audit import create_audit_trail_button
from frontend.pages.jobs.components import (
    render_error_status,
    render_job_metadata,
    render_model_info,
    render_job_action_buttons,
    render_readonly_form,
    render_compact_inputs_summary
)
from frontend.pages.jobs.job_utils import extract_job_fields
from frontend.pages.chatbot.utils.ui_operations import UIOperations
from frontend.utils.theme import apply_saved_theme

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def _maybe_render_pipeline_stepper(job_fields: dict) -> None:
    """Show pipeline stepper when this job is one of at least two steps in the same run."""
    uid = job_fields.get("uid")
    if not uid:
        return
    # Prefer stored root; fall back to this job's uid so the SQL ``OR uid = ?`` can still find siblings
    # when older rows only linked the second step to the first job id.
    root = job_fields.get("pipelineRootJobId") or uid
    try:
        from frontend.utils.nicegui_storage import get_user_id_for_jobs

        user_id = get_user_id_for_jobs()
    except Exception:
        user_id = None
    if not user_id:
        return
    try:
        job_db = get_job_db()
        siblings = await job_db.list_jobs_for_pipeline_root(user_id, root)
    except Exception as e:
        logger.debug("Pipeline sibling load failed: %s", e)
        return
    if len(siblings) < 2:
        return
    from frontend.components.jobs.pipeline_run_banner import render_pipeline_run_banner

    steps = [{"job_id": s.uid, "endpoint": s.endpoint or ""} for s in siblings]
    canonical_root = siblings[0].uid if siblings else root
    render_pipeline_run_banner(
        root_job_id=canonical_root, current_job_id=uid, steps=steps
    )


@ui.page('/jobs/{job_id}')
async def job_details_page(job_id: str):
    """
    Page route handler for job details.
    
    Displays job details with tabs for outputs and details, including
    job metadata, inputs, parameters, and results.
    
    Args:
        job_id (str): Job unique identifier
    
    Returns:
        None: Page is rendered directly
    """
    #logger.info("Job details page accessed for job: %s", job_id)
    apply_saved_theme()
    create_navbar()
    from frontend.utils.demo_user_gate import require_demo_user_session

    if not require_demo_user_session():
        return

    # Load job data from local database
    try:
        #logger.debug("Fetching job data for job_id: %s", job_id)
        job_db = get_job_db()
        job = await job_db.get_job_by_uid(job_id)
        if not job:
            logger.error("Job %s not found", job_id)
            ui.label(f'Job not found: {job_id}').classes('text-red-600')
            return
        #logger.info("Job data loaded successfully")
    except Exception as e:
        logger.error("Error loading job %s: %s", job_id, str(e))
        ui.label(f'Error loading job: {str(e)}').classes('text-red-600')
        return
    
    # items-stretch overrides NiceGUI .nicegui-tab-panel { align-items: flex-start } so tab content fills width
    with ui.column().classes('w-full max-w-full min-w-0 items-stretch px-4 sm:px-6 lg:px-8 py-8'):
        # Breadcrumbs
        job_fields = extract_job_fields(job)
        endpoint = job_fields.get('endpoint')
        model_uid = job_fields.get('modelUid')
        
        # Breadcrumb navigation (single row; tabs distinguish Outputs vs Details)
        create_breadcrumbs(
            [
                {'label': 'Jobs', 'link': '/jobs'},
                {'label': f'Job {job_id}'},
            ]
        )

        await _maybe_render_pipeline_stepper(job_fields)

        # Header (use shared page header component)
        try:
            from frontend.components.shared.page_header import render_page_header

            def _header_actions():
                ui.link('Back to Jobs', '/jobs').classes('text-indigo-600 hover:underline')
            # actions_callable=_header_actions
            render_page_header(f'Job Results')
        except Exception:
            with ui.row().classes('items-center justify-between mb-6'):
                ui.label(f'Job {job_id}').classes('text-3xl font-bold')
                with ui.row().classes('gap-2'):
                    ui.link('Back to Jobs', '/jobs').classes('text-indigo-600 hover:underline')
        
        # Tabs
        with ui.tabs().classes('w-full mb-4') as tabs:
            ui.tab('Outputs')
            ui.tab('Details')
        
        # Failed jobs with no stored response: error text lives under Details with metadata;
        # open that tab first and avoid duplicating a large "Outputs" error card.
        _open_details = (
            str(job_fields.get("status") or "") == "Failed"
            and not job_fields.get("response")
        )
        tab_panels = ui.tab_panels(
            tabs, value="Details" if _open_details else "Outputs"
        ).classes("w-full max-w-full min-w-0")
        
        # Create API client
        api_client = httpx.AsyncClient()
        
        # Outputs tab
        with tab_panels:
            with ui.tab_panel('Outputs').classes('w-full max-w-full min-w-0 !items-stretch'):
                await render_job_outputs(api_client, job)
        
        # Details tab
        with tab_panels:
            with ui.tab_panel('Details').classes('w-full max-w-full min-w-0 !items-stretch'):
                await render_job_details(api_client, job)

        # Long outputs: show the end of the page after render (async previews may settle later).
        try:
            UIOperations.scroll_document_to_bottom()
            for _delay in (0.12, 0.35, 0.75):
                ui.timer(_delay, UIOperations.scroll_document_to_bottom, once=True)
        except Exception:
            pass

async def render_job_outputs(api_client, job):
    """
    Render job outputs.
    
    Displays job results using ResultsPreview when a response exists. Failed jobs
    with no stored response show a short pointer to the Details tab (failure text
    is shown there with metadata).
    
    Args:
        api_client: API client instance for additional requests
        job: JobRecord Pydantic model or dict (for backward compatibility)
    
    Returns:
        None
    
    Tips:
    - Validates response using ResponseBody Pydantic model
    - Shows error card if job failed or no response
    - Includes links to model documentation and run page
    - Supports both JobRecord (Pydantic model) and dict for backward compatibility
    """
    job_fields = extract_job_fields(job)
    job_uid = job_fields['uid']
    response = job_fields['response']
    status = job_fields['status']
    status_text = job_fields['statusText']
    task_schema_dict = job_fields['taskSchema']
    
    # Delegate to extracted component
    try:
        from frontend.components.jobs.job_outputs_card import render_job_outputs_card
        await render_job_outputs_card(
            ui.column().classes('w-full min-w-0 self-stretch'), api_client, job
        )
    except Exception as e:
        logger.exception("Failed to render job outputs via component: %s", e)
        # Fallback to inline renderer
        job_fields = extract_job_fields(job)
        # Re-call original inline for reliability (keeps old behavior)
        # Note: simplest fallback is to re-run original logic; for brevity reuse existing function
        # (This fallback code is intentionally minimal — full fallback handled above in previous iteration.)
        with ui.card().classes('bg-white border border-zinc-300 p-6'):
            ui.label('Results').classes('text-2xl font-bold')

async def render_job_details(api_client, job):
    """
    Render job details including inputs and parameters.
    
    Displays comprehensive job information including metadata, inputs,
    parameters, and model information.
    
    Args:
        api_client: API client instance for fetching model info
        job: JobRecord Pydantic model or dict (for backward compatibility)
    
    Returns:
        None
    
    Tips:
    - Timestamps are formatted from ISO format
    - Status is color-coded
    - Model information is fetched if model_uid is available
    - Inputs and parameters are displayed in organized sections
    - Supports both JobRecord (Pydantic model) and dict for backward compatibility
    """
    job_fields = extract_job_fields(job)
    job_uid = job_fields['uid']
    request_body_dict = job_fields['request']
    task_schema_dict = job_fields['taskSchema']
    
    #logger.info("Rendering job details for job: %s", job_uid)
    try:
        # Delegate to extracted job details panel component
        from frontend.components.jobs.job_details_panel import render_job_details_panel
        await render_job_details_panel(ui.column().classes('w-full max-w-full min-w-0'), api_client, job_fields)
    except Exception as e:
        logger.exception("Failed to render job details via component: %s", e)
        # Fallback inline rendering for compatibility
        try:
            with ui.card().classes('bg-white border border-zinc-300 p-6'):
                with ui.column().classes('gap-4'):
                    ui.label('Job Information').classes('text-2xl font-bold')
                    render_job_metadata(job_fields)
                    await render_model_info(api_client, job_fields)
                    if task_schema_dict:
                        try:
                            task_schema = TaskSchema(**task_schema_dict) if isinstance(task_schema_dict, dict) else task_schema_dict
                            request_body = RequestBody(**request_body_dict) if isinstance(request_body_dict, dict) else request_body_dict
                            render_readonly_form(task_schema, request_body)
                        except Exception as e2:
                            logger.error("Error parsing schema in fallback: %s", str(e2))
                            ui.label(f'Error parsing schema: {str(e2)}').classes('text-red-600')
        except Exception as e2:
            logger.exception("Error rendering job details fallback: %s", e2)
            ui.label(f'Error rendering details: {str(e2)}').classes('text-red-600')