"""
Chatbot Form Handlers

This module provides orchestration functions for handling forms, tool picker,
form submission, and results display in the chatbot interface.

Components have been extracted to separate modules:
- constants.py: FormConfig class with styling constants
- pickers.py: ToolPicker and AnalysisPicker classes
- results.py: ResultRenderer for popups and non-chat result views
"""

import asyncio
import logging
from nicegui import ui
from typing import Any, Callable, List, Optional
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.config import ToolRegistry
from frontend.utils.error_handling import handle_api_error, show_error_to_user
from frontend.pages.chatbot.constants import FormConfig
from frontend.pages.chatbot.pickers import ToolPicker, AnalysisPicker
from frontend.utils.nicegui_storage import get_user_id
from frontend.pages.chatbot.utils.safe_ui import is_ephemeral_ui_error

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Per-session chat container references (keyed by user_id from get_user_id).
# Ensures selection messages render into the correct user's chat area when
# multiple concurrent browser clients are connected.
_CHAT_CONTAINERS_BY_USER: dict[str, ui.element] = {}

def set_global_chat_container(container: ui.element):
    """Store chat container for the current session (browser client)."""
    user_id = get_user_id()
    if user_id:
        _CHAT_CONTAINERS_BY_USER[user_id] = container
        logger.debug("Stored chat container for user %s", user_id[:16] + "..." if len(user_id) > 16 else user_id)
    else:
        logger.warning("No user_id available; chat container not stored for session")

def get_global_chat_container() -> Optional[ui.element]:
    """Get chat container for the current session (browser client)."""
    user_id = get_user_id()
    if user_id:
        return _CHAT_CONTAINERS_BY_USER.get(user_id)
    return None

async def show_tool_picker(
    container: ui.element,
    tool_registry: ToolRegistry,
    on_tool_selected: Callable[[str, dict], None]
):
    """
    Show tool picker menu using the refactored ToolPicker class.

    Displays a UI for selecting tools by number from the tool registry.
    User can select a tool by entering its number.

    Args:
        container (ui.element): Container to add tool picker to
        tool_registry (ToolRegistry): Tool registry with available tools
        on_tool_selected (Callable): Callback function called with (endpoint, {})
            when a tool is selected

    Returns:
        None

    Tips:
        - Tools are displayed in a table format
        - Tool selection triggers form loading for that tool
        - Uses ToolRegistry.TOOL_MENU for available tools
    """
    picker = ToolPicker(container, tool_registry, on_tool_selected)
    await picker.show()


async def show_analysis_picker(
    container: ui.element,
    on_analysis_selected: Callable[[str], None]
):
    """
    Show analysis type picker menu using the refactored AnalysisPicker class.

    Displays a UI for selecting what type of analysis the user wants to perform.
    User can select from predefined analysis options.

    Args:
        container (ui.element): Container to add analysis picker to
        on_analysis_selected (Callable): Callback function called with analysis type

    Returns:
        None
    """
    picker = AnalysisPicker(container, on_analysis_selected)
    await picker.show()


async def show_tool_selection(container: ui.element, endpoint: str):
    """
    Show tool selection message.
    
    Displays a message indicating which tool was selected for the user.
    
    Args:
        container (ui.element): Container to add message to
        endpoint (str): Selected tool endpoint
    
    Returns:
        None
    """
    logger.debug("Showing tool selection message for endpoint: %s", endpoint)
    # Safety: ensure container's client still exists
    try:
        _ = container.client
    except RuntimeError as e:
        if is_ephemeral_ui_error(e):
            logger.warning("Skipping tool selection: UI client was deleted")
            return
        raise
    logger.debug("Showing tool selection message for endpoint: %s", endpoint)
    try:
        from frontend.components.results.tool_selection_card import render_tool_selection_message
    except ImportError as e:
        logger.debug("Tool selection component not available, falling back: %s", e)
        try:
            # Safety: ensure container still valid before creating fallback UI
            _ = container.client
            with container:
                with ui.card().classes(
                    'w-full max-w-2xl bg-white ring-1 ring-zinc-200 shadow-sm rounded-2xl rounded-tl-none'
                ):
                    with ui.column().classes('p-4 gap-2 w-full min-w-0'):
                        ui.label('Assistant').classes(
                            'font-semibold !text-sm text-zinc-500 uppercase tracking-wide'
                        )
                        ui.label(
                            f"Running {ToolRegistry.display_name_for_endpoint(endpoint)} operation."
                        ).classes(
                            '!text-base sm:!text-lg leading-snug text-zinc-800'
                        )
            logger.debug("Tool selection message displayed (fallback)")
        except RuntimeError:
            logger.warning("Skipping fallback tool selection: UI client was deleted")
    else:
        # try to render using the component; if it fails, fall back silently
        try:
            render_tool_selection_message(container, endpoint)
            logger.debug("Tool selection message displayed via component")
        except (RuntimeError, AttributeError, OSError) as e:
            logger.debug("Tool selection component failed to render, falling back: %s", e)


async def load_and_show_form(
    container: ui.element,
    core: ChatbotCore,
    endpoint: str,
    arguments: dict,
    on_form_submit: Callable,
    on_form_cancel: Optional[Callable] = None
) -> Optional[ui.element]:
    """
    Load task schema and show form.
    
    Fetches the task schema for the endpoint, converts arguments to initial
    values, shows tool selection message, and creates the input form for user to fill out.
    
    Args:
        container (ui.element): Container to add form to
        core (ChatbotCore): ChatbotCore instance for API calls
        endpoint (str): API endpoint name
        arguments (dict): Tool call arguments to pre-fill form
        on_form_submit (Callable): Callback for form submission
    
    Returns:
        Optional[ui.element]: The form card element, or None if form loading failed
    
    Tips:
    - Arguments are normalized and converted to form initial values
    - Tool selection message informs user which tool was selected
    - Form submission triggers on_form_submit callback
    """
    logger.debug("Loading form for endpoint: %s", endpoint)
    logger.debug("load_and_show_form invocation: provided_container=%r global_chat_container=%r", container, get_global_chat_container())
    logger.debug("Form arguments: %s", arguments)
    # If no container provided, try to render into the input area as a safer default
    if container is None:
        try:
            from frontend.components.chat.input_area import get_latest_input_area
            ia = get_latest_input_area()
            if ia is not None:
                container = ia
                logger.debug("No container passed; using latest input area container: %r", container)
        except Exception:
            logger.debug("No latest input area available; will use provided container or chat area")
    
    try:
        # Safety: ensure container's client still exists before doing UI work
        try:
            _ = container.client
        except RuntimeError as e:
            if is_ephemeral_ui_error(e):
                logger.warning("Skipping form load: UI client was deleted")
                return None
            raise

        task_schema = await core.get_task_schema_from_endpoint(endpoint)
        if not task_schema:
            error_msg = f"No task schema found for endpoint: {endpoint}"
            logger.warning(error_msg)
            show_error_to_user(error_msg)
            return None
        
        try:
            initial_values = core.convert_arguments_to_initial_values(arguments, task_schema, endpoint)
            logger.debug("Initial values converted: %d inputs, %d parameters",
                        len(initial_values.get('inputs', {})), len(initial_values.get('parameters', {})))
        except (ValueError, TypeError) as e:
            # Conversion failures are expected for malformed arguments; fall back to empty initial values
            logger.warning("Failed to convert arguments to initial values: %s, using empty values", str(e))
            initial_values = {}
        
        # Tool selection + form share one parent column that fades in after layout (less flicker
        # than painting the selection card and form in separate layout passes).
        logger.debug("load_and_show_form called: endpoint=%s arguments=%s", endpoint, arguments)
        render_container = container or get_global_chat_container()
        reveal_outer = None
        try:
            if render_container is not None:
                with render_container:
                    reveal_outer = ui.column().classes(FormConfig.FORM_REVEAL_OUTER_CLASSES)
        except RuntimeError:
            reveal_outer = None

        selection_card = None
        selection_target = reveal_outer if reveal_outer is not None else render_container
        try:
            from frontend.components.results.tool_selection_card import render_tool_selection_message
            try:
                global_container = get_global_chat_container()
                target_for_selection = selection_target or container or global_container
                logger.debug(
                    "Rendering tool selection message into container=%r (explicit=%s global_fallback=%s)",
                    target_for_selection,
                    container is not None,
                    bool(global_container) and container is None,
                )
                if target_for_selection is not None:
                    selection_card = render_tool_selection_message(target_for_selection, endpoint)
            except (RuntimeError, AttributeError, OSError) as e:
                logger.warning("Failed to render tool selection card component: %s", str(e))
                selection_card = None
        except ImportError as e:
            logger.debug("Tool selection component not available: %s", e)
            try:
                await show_tool_selection(container or get_global_chat_container(), endpoint)
            except RuntimeError:
                logger.warning("Failed to show tool selection message: fallback also failed")

        try:
            if reveal_outer is not None:
                with reveal_outer:
                    wrapper = ui.column().classes('w-full rb-form-wrapper')
            elif render_container is not None:
                with render_container:
                    wrapper = ui.column().classes('w-full rb-form-wrapper')
            else:
                wrapper = ui.column().classes('w-full rb-form-wrapper')
        except RuntimeError:
            wrapper = ui.column().classes('w-full rb-form-wrapper')

        # Create form and add to wrapper
        # Note: on_submit callback receives (request_body, endpoint, task_schema)
        try:
            # If arguments include a resolved filter id, wrap the on_form_submit callback
            # so that the resulting request_body will include the filterId in parameters.
            filter_id_for_form = None
            try:
                filter_id_for_form = arguments.get('filterId') or arguments.get('_resolved_filter_id')
            except Exception:
                filter_id_for_form = None

            async def _on_submit_wrapper(request_body, ep, ts):
                try:
                    if filter_id_for_form:
                        try:
                            # Ensure request_body has parameters mapping
                            if isinstance(request_body, dict):
                                params = request_body.get('parameters') or {}
                                if not isinstance(params, dict):
                                    params = {}
                                meta = params.get('_meta') or {}
                                if not isinstance(meta, dict):
                                    meta = {}
                                meta['filterId'] = filter_id_for_form
                                params['_meta'] = meta
                                request_body['parameters'] = params
                            else:
                                # request_body may be a pydantic model with .parameters
                                try:
                                    params = getattr(request_body, 'parameters', None) or {}
                                    if not isinstance(params, dict):
                                        params = {}
                                    meta = params.get('_meta') or {}
                                    if not isinstance(meta, dict):
                                        meta = {}
                                    meta['filterId'] = filter_id_for_form
                                    params['_meta'] = meta
                                    request_body.parameters = params
                                except Exception:
                                    pass
                        except Exception:
                            # best-effort, don't block submission
                            pass
                    # Call original submit handler
                    return await on_form_submit(request_body, ep, ts)
                except Exception:
                    # Propagate exceptions to caller
                    raise

            with wrapper:
                form_card = await core.create_input_form(
                    task_schema=task_schema,
                    endpoint=endpoint,
                    initial_values=initial_values,
                    on_submit=_on_submit_wrapper,
                    on_cancel=on_form_cancel
                )
            # Attach selection_card to the form_card so the Cancel handler can remove it directly.
            try:
                if selection_card is not None and form_card is not None:
                    setattr(form_card, '_related_tool_selection_card', selection_card)
            except (AttributeError, TypeError):
                pass
            if reveal_outer is not None:
                await asyncio.sleep(FormConfig.FORM_REVEAL_YIELD_S)
                try:
                    reveal_outer.classes(remove='opacity-0', add='opacity-100')
                except Exception:
                    pass
            logger.debug("Form loaded and displayed for endpoint: %s (container=%r)", endpoint, wrapper)
            logger.debug("selection_card=%r form_card=%r", selection_card, form_card)
            return form_card
        except (RuntimeError, ValueError, TypeError, OSError) as e:
            logger.error("Failed to create input form: %s", str(e))
            show_error_to_user(f"Failed to create form: {str(e)}")
            return None
        
    except (RuntimeError, ValueError, TypeError, OSError) as e:
        logger.error("Failed to load form for endpoint %s: %s", endpoint, str(e))
        await handle_api_error(e, f"Error loading form for {endpoint}", 
                              user_message=f"Failed to load form: {str(e)}")
        return None


async def show_results(
    container: ui.element,
    response_body,
    job_id: Optional[str] = None,
    *,
    pipeline_total_steps: Optional[int] = None,
    remaining_calls_after_step: Optional[List[Any]] = None,
    pipeline_root_job_id: Optional[str] = None,
    pipeline_user_id: Optional[str] = None,
):
    """
    Show a compact “job completed” strip with one green button to open full results on the job page.

    ``response_body`` is kept for API compatibility with callers; rendering does not depend on its shape.
    """
    # More steps queued after this job → pipeline step, not the final completion (no "View results" yet).
    _rem = remaining_calls_after_step
    is_intermediate = bool(_rem is not None and len(_rem) > 0)
    completed_step = None
    next_step = None
    if is_intermediate and pipeline_total_steps is not None and _rem is not None:
        completed_step = pipeline_total_steps - len(_rem)
        next_step = completed_step + 1
    show_view_job = bool(job_id and not is_intermediate)

    logger.debug(
        "Showing results (job_id: %s, intermediate_pipeline: %s, show_view_job: %s)",
        job_id,
        is_intermediate,
        show_view_job,
    )
    # Safety check: ensure the container is still valid (client not deleted)
    try:
        if container is not None:
            _ = container.client
    except RuntimeError as e:
        if is_ephemeral_ui_error(e):
            logger.warning("Skipping result display: UI client was deleted (likely page refresh or navigation)")
            return
        raise

    _uid = pipeline_user_id or get_user_id()
    from frontend.utils.pipeline_index_context import pipeline_index_scope

    try:
        with pipeline_index_scope(pipeline_root_job_id, _uid):
            await _show_results_body(
                container,
                response_body,
                job_id,
                is_intermediate=is_intermediate,
                completed_step=completed_step,
                next_step=next_step,
                pipeline_total_steps=pipeline_total_steps,
                remaining_calls_after_step=remaining_calls_after_step,
                show_view_job=show_view_job,
            )
    except (RuntimeError, ValueError, TypeError, OSError) as e:
        logger.error("Error showing modern results: %s", str(e))
        show_error_to_user(f"Failed to show results: {str(e)}")


async def _show_results_body(
    container: ui.element,
    response_body,
    job_id: Optional[str],
    *,
    is_intermediate: bool,
    completed_step: Optional[int],
    next_step: Optional[int],
    pipeline_total_steps: Optional[int],
    remaining_calls_after_step: Optional[List[Any]],
    show_view_job: bool,
) -> None:
    """Green-accent card: pipeline step status, or final job line + View results (final step only)."""
    del response_body, show_view_job  # API compatibility / unused
    try:
        with container:
            # rb-job-result-anchor: scroll helpers target this after async render
            with ui.card().classes(
                'rb-job-result-anchor w-full max-w-md rounded-xl border-2 border-green-400 '
                'bg-gradient-to-br from-green-50 to-emerald-50 p-4 shadow-sm flex flex-col gap-3'
            ):
                if is_intermediate:
                    if completed_step and pipeline_total_steps and next_step:
                        ui.label(
                            f'Step {completed_step} of {pipeline_total_steps} complete, continuing to step {next_step}.'
                        ).classes('text-sm text-green-900')
                    else:
                        ui.label('Pipeline step finished. Continuing…').classes(
                            'text-sm text-green-900'
                        )
                else:
                    ui.label('Job completed').classes('text-base font-semibold text-green-900')

                # Open job/results only after the last step (no remaining pipeline calls).
                if job_id and not is_intermediate:

                    def _open_results(_jid: str = job_id) -> None:
                        ui.navigate.to(f'/jobs/{_jid}')

                    ui.button(
                        'View results',
                        icon='open_in_new',
                        on_click=_open_results,
                    ).classes(
                        'w-full bg-green-600 hover:bg-green-700 text-white '
                        'font-medium py-3 rounded-lg shadow-sm'
                    )
                elif not job_id and not is_intermediate:
                    ui.label('Open Jobs from the menu to see run details.').classes('text-sm text-zinc-600')

        logger.debug('Job completion banner rendered (View results -> /jobs/%s)', job_id)
    except (RuntimeError, ValueError, TypeError, OSError) as e:
        logger.error("Error in results body: %s", str(e))
        raise
