"""
Chatbot Form Handlers

This module provides orchestration functions for handling forms, tool picker,
form submission, and results display in the chatbot interface.

Components have been extracted to separate modules:
- constants.py: FormConfig class with styling constants
- pickers.py: ToolPicker and AnalysisPicker classes
- results.py: ResultRenderer class for result display
"""

import logging
from nicegui import ui
from typing import Optional, Callable
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.config import ToolRegistry
from frontend.utils.error_handling import handle_api_error, show_error_to_user
from frontend.pages.chatbot.constants import FormConfig
from frontend.pages.chatbot.pickers import ToolPicker, AnalysisPicker
from frontend.pages.chatbot.utils.ui_styling import UIStyling
from frontend.pages.chatbot.results import ResultRenderer

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Global chat container reference (set by ChatbotPage.render) to ensure selection messages
# always render into the main chat area even if callers pass an input-area container.
_GLOBAL_CHAT_CONTAINER = None

def set_global_chat_container(container: ui.element):
    global _GLOBAL_CHAT_CONTAINER
    _GLOBAL_CHAT_CONTAINER = container

def get_global_chat_container() -> Optional[ui.element]:
    return _GLOBAL_CHAT_CONTAINER

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
        if 'deleted' in str(e):
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
                with ui.card().classes('w-full max-w-sm bg-blue-50 shadow-sm'):
                    with ui.row().classes('p-3 items-center gap-2 flex-wrap'):
                        ui.label('🤖 Assistant').classes('font-medium text-sm')
                        ui.label(f"I'll use {endpoint} to help you.").classes('')
                        ui.label('🔧 Selected Tool').classes('font-medium text-sm')
                        ui.label(endpoint).classes('text-sm text-gray-600')
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
    on_form_submit: Callable
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
    logger.info("Loading form for endpoint: %s", endpoint)
    logger.info("load_and_show_form invocation: provided_container=%r global_chat_container=%r", container, get_global_chat_container())
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
            if 'deleted' in str(e):
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
            logger.info("Initial values converted: %d inputs, %d parameters",
                        len(initial_values.get('inputs', {})), len(initial_values.get('parameters', {})))
        except (ValueError, TypeError) as e:
            # Conversion failures are expected for malformed arguments; fall back to empty initial values
            logger.warning("Failed to convert arguments to initial values: %s, using empty values", str(e))
            initial_values = {}
        
        # Show tool selection message first, then create a wrapper for the input form
        # so the visual order is: assistant/tool-selection -> input form.
        logger.info("load_and_show_form called: endpoint=%s container=%r arguments=%s", endpoint, container, arguments)
        selection_card = None
        try:
            from frontend.components.results.tool_selection_card import render_tool_selection_message
            try:
                # Determine render container (prefer global chat container)
                global_container = get_global_chat_container()
                target_for_selection = global_container or container
                logger.info("Rendering tool selection message into container=%r (global_in_use=%s)", target_for_selection, bool(global_container))
                selection_card = render_tool_selection_message(target_for_selection, endpoint)
            except (RuntimeError, AttributeError, OSError) as e:
                logger.warning("Failed to render tool selection card component: %s", str(e))
                selection_card = None
        except ImportError as e:
            logger.debug("Tool selection component not available: %s", e)
            try:
                # Fallback: render into container (or global container if available)
                await show_tool_selection(get_global_chat_container() or container, endpoint)
            except RuntimeError:
                logger.warning("Failed to show tool selection message: fallback also failed")

        # Now create a dedicated wrapper so the selection message and form are grouped together,
        # and the wrapper is inserted immediately after the selection card in the same container.
        try:
            render_container = get_global_chat_container() or container
            if render_container is not None:
                with render_container:
                    wrapper = ui.column().classes('w-full')
            else:
                wrapper = ui.column().classes('w-full')
        except RuntimeError:
            wrapper = ui.column().classes('w-full')

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
                    on_submit=_on_submit_wrapper
                )
            # Attach selection_card to the form_card so the Cancel handler can remove it directly.
            try:
                if selection_card is not None and form_card is not None:
                    setattr(form_card, '_related_tool_selection_card', selection_card)
            except (AttributeError, TypeError):
                pass
            logger.info("Form loaded and displayed for endpoint: %s (container=%r)", endpoint, wrapper)
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
    job_id: Optional[str] = None
):
    """
    Show job results with modern expandable interface using ResultRenderer.

    Displays job results using a modern, expandable interface that prevents
    overlap and provides better organization of result types.

    Args:
        container (ui.element): Container to add results to
        response_body: ResponseBody Pydantic model with results
        job_id (Optional[str]): Job ID (currently unused, for future use)

    Returns:
        None

    Tips:
        - Results are displayed in expandable sections to prevent overlap
        - Each result type has its own popup dialog for detailed viewing
        - Modern card design with hover effects and smooth transitions
    """
    logger.info("Showing results with modern interface (job_id: %s)", job_id)
    # Safety check: ensure the container is still valid (client not deleted)
    try:
        if container is not None:
            _ = container.client
    except RuntimeError as e:
        if 'deleted' in str(e):
            logger.warning("Skipping result display: UI client was deleted (likely page refresh or navigation)")
            return
        raise

    try:
        with container:
            # Modern success card with gradient
            with ui.card().classes(FormConfig.SUCCESS_CARD_CLASSES):
                with ui.column().classes('p-6'):
                    # Success header with icon and job info
                    ResultRenderer.create_success_header(job_id)

                    # Get response data
                    response_dict = response_body.model_dump() if hasattr(response_body, 'model_dump') else response_body
                    logger.debug("Response dict keys: %s", list(response_dict.keys()) if isinstance(response_dict, dict) else type(response_dict))
                    logger.debug("Response dict: %s", response_dict)

                    # Handle both response formats:
                    # 1. {'root': {'output_type': 'batchtext', ...}} - wrapped in root
                    # 2. {'output_type': 'batchtext', ...} - direct root object
                    if 'root' in response_dict:
                        root = response_dict['root']
                        logger.debug("Using wrapped root format")
                    else:
                        root = response_dict
                        logger.debug("Using direct root format")

                    logger.debug("Root data: %s", root)

                    # Validate response data
                    if not root or not isinstance(root, dict):
                        logger.error("Invalid response: root is empty or not a dict")
                        ResultRenderer.show_error_message(
                            'Invalid response format',
                            'The server returned an incomplete response. Please try again or contact support.',
                            response_dict
                        )
                        return

                    # Determine result type and create appropriate display
                    result_type = root.get('output_type', 'unknown')
                    logger.debug("Result type: %s", result_type)

                    if not result_type or result_type == 'unknown':
                        logger.error("Invalid response: missing output_type in root")
                        ResultRenderer.show_error_message(
                            'Invalid response format',
                            'The server response is missing required information. Please try again.',
                            root
                        )
                        return

                    result_count = ResultRenderer.get_result_count(root)
                    result_title = ResultRenderer.get_result_title(result_type, result_count)

                    # Main result card with click-to-expand
                    async def show_result_details():
                        await ResultRenderer.show_result_popup(root, result_type, result_title, response_dict)

                    # Pass job_id into result card so it can render its inline action button if applicable
                    # If this result is associated with a job, render the tool_result card (which shows "✅ Result")
                    if job_id:
                        try:
                            from frontend.components.chat.tool_result_card import render_tool_result_card
                            # render the tool result card and include the inline View Job button
                            render_tool_result_card(ui.column(), result_title, UIStyling, job_id=job_id)
                        except (ImportError, RuntimeError, AttributeError) as e:
                            logger.debug("Failed to render tool_result_card for job_id %s: %s", job_id, e)
                            ResultRenderer.create_result_card(result_type, result_title, result_count, show_result_details)
                    else:
                        ResultRenderer.create_result_card(result_type, result_title, result_count, show_result_details)

        logger.debug("Modern results interface displayed successfully")
    except (RuntimeError, ValueError, TypeError, OSError) as e:
        logger.error("Error showing modern results: %s", str(e))
        show_error_to_user(f"Failed to show results: {str(e)}")
