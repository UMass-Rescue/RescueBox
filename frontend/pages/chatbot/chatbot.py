"""
Chatbot Page

This module provides the ChatbotPage class for the RescueBox Assistant interface.
It orchestrates UI rendering, message processing, form display, job submission, and
results presentation using the chatbot core components and specialized modules.

The ChatbotPage class now uses extracted components for better separation of concerns:
- state.ChatbotStateManager: Manages conversation state and messages
- state.ChatbotEventHandler: Coordinates UI events and callbacks
- handlers.MessageProcessor: Handles message sending and processing
- handlers.ResultProcessor: Processes handler results and coordinates actions
- handlers.FormSubmitHandler: Handles form submission and job execution
"""

import logging
import asyncio
from nicegui import ui
from typing import Optional
from frontend.components.shared import create_navbar
from frontend.chatbot.config import ChatbotConfig, ToolRegistry
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.message_handler import MessageHandler

# Import specialized modules
from frontend.pages.chatbot.chatbot_message import ChatMessage, render_message, show_error_message
from frontend.pages.chatbot.chatbot_ui import create_chat_ui
from frontend.pages.chatbot.chatbot_forms import load_and_show_form, show_results

# Import refactored components
from frontend.pages.chatbot.state import ChatbotStateManager, ChatbotEventHandler
from frontend.pages.chatbot.handlers import MessageFlowCoordinator

# Import common utilities (only what's used here)
from frontend.pages.chatbot.utils import (
    UIOperations, CallbackManager, ConversationLoader
)
from frontend.utils.nicegui_storage import set_current_conversation_id
from frontend.database import get_chat_history_db, get_job_db, JobStatus

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class ChatbotPage:
    """
    Chatbot page for RescueBox Assistant.

    This class orchestrates the chatbot UI and functionality using extracted
    components for better separation of concerns and maintainability.

    Usage:
        page = ChatbotPage()
        await page.render()

    Attributes:
        config (ChatbotConfig): Configuration for the chatbot
        core (ChatbotCore): Core chatbot functionality
        message_handler (MessageHandler): Message processing handler
        tool_registry (ToolRegistry): Registry of available tools

        # Extracted components
        state_manager (ChatbotStateManager): Manages conversation state
        event_handler (ChatbotEventHandler): Coordinates UI events
        message_processor (MessageProcessor): Handles message operations
        result_processor (ResultProcessor): Processes handler results
        form_handler (FormSubmitHandler): Handles form submissions
    """

    def __init__(self, config: Optional[ChatbotConfig] = None):
        """
        Initialize the ChatbotPage with extracted components.

        Args:
            config (Optional[ChatbotConfig]): Configuration for the chatbot.
                If None, creates a default configuration.
        """
        logger.info("Initializing ChatbotPage")

        # Configuration and core components
        self.config = config or ChatbotConfig()
        self.core = ChatbotCore(self.config)
        self.message_handler = MessageHandler(self.core, self.config)
        self.tool_registry = ToolRegistry()

        # Initialize extracted components
        self.state_manager = ChatbotStateManager()
        self.event_handler = ChatbotEventHandler(self.state_manager)
        self.callback_manager = CallbackManager(self)
        self.conversation_loader = ConversationLoader(self)

        # Initialize unified message flow coordinator
        self.message_flow_coordinator = MessageFlowCoordinator(self.state_manager, self.load_and_show_form)
        self.message_flow_coordinator.set_message_handler(self.message_handler)
        self.message_flow_coordinator.set_tool_registry(self.tool_registry)

        # Keep backward compatibility aliases for existing code
        self.message_processor = self.message_flow_coordinator.message_processor
        self.result_processor = self.message_flow_coordinator.result_processor
        self.form_handler = self.message_flow_coordinator.form_submit_handler

        # UI components (will be set during render)
        self.chat_container = None
        self.input_field = None

        logger.debug("ChatbotPage initialized with extracted components")
        self.status_text = ''
        self.job_progress = 0.0
        logger.debug("ChatbotPage initialized successfully")
    
    async def render(self):
        """
        Render the chatbot UI using extracted components.

        Creates the complete chatbot interface with proper event binding
        and state management.

        Returns:
            None: UI is added directly to the current context
        """
        logger.info("Rendering chatbot UI")

        # Set up event handler callbacks
        self.event_handler.set_callbacks(
            send_callback=self._handle_send_message
        )

        # Create UI and bind events
        self.chat_container, self.input_field, self.status_label = create_chat_ui(
            on_send=self.event_handler.handle_send_message,
            on_new_conversation=self._handle_new_conversation,
            tool_registry=self.tool_registry,
            core=self.core,
            form_submit_handler=self.form_handler,
            status_text_ref=self.state_manager,
            state_manager=self.state_manager
        )

        # Set UI components in event handler
        self.event_handler.set_ui_components(
            input_field=self.input_field,
            chat_container=self.chat_container
        )
        # Give the message flow coordinator access to the chat container so it can
        # render assistant messages and forms into the conversation area (not the input area).
        try:
            setattr(self.message_flow_coordinator, 'chat_container', self.chat_container)
        except Exception:
            pass

        # Bind events
        self.event_handler.bind_events()


        # Set input field in state manager
        self.state_manager.set_input_field(self.input_field)

        logger.info("Chatbot UI rendered successfully")
        # Ensure a conversation exists for this session (create if missing)
        try:
            if not self.state_manager.conversation_id:
                chat_history = get_chat_history_db()
                conversation = await chat_history.create_conversation(title="Chatbot Session")
                conv_id = conversation.conversation_id
                self.state_manager.set_conversation_id(conv_id)
                # Persist to NiceGUI storage (or fallback test storage)
                set_current_conversation_id(conv_id)
                logger.info("Initialized new conversation on page load: %s", conv_id)
        except Exception as e:
            logger.warning("Failed to auto-create conversation on load: %s", e)

        # After conversation exists, try to reload recent job/result into chat
        try:
            await self._reload_recent_job_into_chat()
        except Exception as e:
            logger.debug("No recent job reload performed: %s", e)

    async def load_conversation_from_data(self, conversation_data: dict):
        """
        Load a conversation from stored data.

        Args:
            conversation_data: Dictionary containing conversation_id, conversation_data, and messages
        """
        await self.conversation_loader.load_conversation(conversation_data)

    async def _re_run_tool(self, endpoint: str, arguments: dict):
        """
        Re-run a tool with the given endpoint and arguments.

        Args:
            endpoint: Tool endpoint name
            arguments: Tool arguments dictionary
        """
        logger.info("Re-running tool: %s with args: %s", endpoint, arguments)

        try:
            # Attempt to find the input area container to render the form there
            input_area_container = None
            try:
                # Prefer the module-level getter for the latest input area (most reliable).
                try:
                    from frontend.components.chat.input_area import get_latest_input_area
                    ia = get_latest_input_area()
                    if ia is not None:
                        input_area_container = ia
                except Exception:
                    input_area_container = None

                # Fallback: try to find an ancestor that looks like the input area
                if input_area_container is None:
                    input_el = getattr(self, 'input_field', None)
                    ancestor = getattr(input_el, 'parent', None)
                    while ancestor:
                        if hasattr(ancestor, 'input_field'):
                            input_area_container = ancestor
                            break
                        ancestor = getattr(ancestor, 'parent', None)
            except Exception:
                input_area_container = None
            # Use the input area when available, otherwise fall back to chat container
            logger.debug("_re_run_tool: found input_area_container=%r; calling load_and_show_form", input_area_container)
            await self.load_and_show_form(endpoint, arguments, container=input_area_container)
            logger.info("Tool re-run initiated successfully: %s", endpoint)
        except Exception as e:
            logger.error("Error re-running tool %s: %s", endpoint, str(e))
            # Note: ui.notify removed because this runs in background task without UI context
    
    
    async def _handle_send_message(self):
        """
        Handle sending a user message using the unified message flow coordinator.
        """
        message_text = self.input_field.value.strip()
        if not message_text:
            return

        # Scroll to bottom immediately when send is clicked
        await self.scroll_to_bottom()

        # Process message using unified coordinator
        # This handles the complete flow: message → processing → results → forms
        await self.message_flow_coordinator.process_user_message(
            message_text=message_text,
            input_field=self.input_field,
            is_processing_ref={'value': False},  # TODO: Get from actual state
            add_message_func=self._add_message,
            show_error_func=self._show_error,
            update_status_func=self._update_status,
            core=self.core
        )

        # Scroll to bottom after message processing completes to keep input area visible
        await self.scroll_to_bottom()

    async def scroll_to_bottom(self):
        """
        Scroll the page to the bottom to keep the input area visible.
        """
        UIOperations.scroll_to_bottom()

    async def new_conversation(self):
        """
        Create a new conversation and update state/storage.
        """
        try:
            # Reset in-memory state
            self.state_manager.reset_conversation()

            # Create a conversation in the DB
            from frontend.database import get_chat_history_db
            chat_history = get_chat_history_db()
            conversation = await chat_history.create_conversation(title="New Conversation")
            conv_id = conversation.conversation_id

            # Update state and storage
            self.state_manager.set_conversation_id(conv_id)
            try:
                set_current_conversation_id(conv_id)
            except Exception:
                # Ignore storage errors in test environments
                pass

            logger.info("New conversation created: %s", conv_id)
            return conv_id
        except Exception as e:
            logger.error("Failed to create new conversation: %s", e)
            return None
    @property
    def conversation_id(self):
        """Expose conversation_id for compatibility with tests."""
        try:
            return getattr(self.state_manager, 'conversation_id', None)
        except Exception:
            return None

    async def _process_result(self, result: dict):
        """
        Process handler result using the result processor.

        Args:
            result: Result dictionary from message handler
        """
        # Handle analysis_picker specially
        if result.get('type') == 'analysis_picker':
            async def on_analysis_selected(analysis_type: str):
                await self.scroll_to_bottom()
                # Show loading spinner while Granite model processes
                with self.chat_container:
                    loading_indicator = ui.row().classes('justify-center py-4')
                    with loading_indicator:
                        ui.spinner(size='2rem').classes('text-green-600')
                        ui.label('Analyzing with AI...').classes('ml-2 text-green-700')

                try:
                    # Process analysis with message handler
                    analysis_result = await self.message_handler.handle_smart_analyze(analysis_type)
                    await self._process_result(analysis_result)
                finally:
                    # Remove loading indicator
                    loading_indicator.delete()

            # Process with analysis picker support
            callbacks = self.callback_manager.get_result_processor_callbacks()
            await self.result_processor.process_result(
                result=result,
                container=self.chat_container,
                core=self.core,
                **callbacks
            )
        else:
            # Process normally
            callbacks = self.callback_manager.get_result_processor_callbacks()
            await self.result_processor.process_result(
                result=result,
                container=self.chat_container,
                core=self.core,
                **callbacks
            )

    async def _reload_recent_job_into_chat(self):
        """Reload any running or most-recent finished job into the chat window."""
        try:
            conv_id = self.state_manager.conversation_id
            if not conv_id:
                return
            chat_db = get_chat_history_db()
            messages = await chat_db.get_messages(conv_id)
            # Find most recent tool_result message with job metadata
            target = None
            for msg in reversed(messages):
                if msg.message_type == 'tool_result' and msg.metadata and isinstance(msg.metadata, dict) and msg.metadata.get('job_id'):
                    target = msg
                    break
            if not target:
                return
            job_id = target.metadata.get('job_id')
            # determine endpoint if available on the message
            endpoint = getattr(target, 'tool_call_endpoint', None)
            if not endpoint and getattr(target, 'tool_calls', None):
                try:
                    endpoint = target.tool_calls[0].get('name')
                except Exception:
                    endpoint = None
            # Fetch job record
            job_db = get_job_db()
            job = await job_db.get_job_by_uid(job_id)
            if not job:
                return
            # If running, show a short "job running" message and start polling; if completed, show results
            if getattr(job, 'status', None) == 'Running' or getattr(job, 'status', None) == JobStatus.RUNNING:
                # Show a status message in chat (non-blocking) and start polling
                from frontend.pages.chatbot.chatbot_message import ChatMessage
                self._add_message(ChatMessage('assistant', f"🔄 Job {job_id} is still running..."))
                try:
                    import asyncio as _asyncio
                    _asyncio.create_task(self._poll_job_status(job_id, endpoint))
                except Exception:
                    logger.debug("Failed to start background poll for job %s", job_id)
            elif getattr(job, 'status', None) == 'Completed' or getattr(job, 'status', None) == JobStatus.COMPLETED:
                # Show stored results
                try:
                    # If the conversation already contains the tool_result message with this job_id (we found 'target'),
                    # skip duplicative show_results rendering and rely on history-rendered messages instead.
                    if target:
                        logger.debug("Job %s already present in conversation messages; skipping duplicate show_results()", job_id)
                    else:
                        await show_results(self.chat_container, job.response, job_id)
                except Exception as e:
                    logger.warning("Failed to render stored job results %s: %s", job_id, e)
        except Exception as e:
            logger.debug("Error reloading recent job into chat: %s", e)
    
    async def _poll_job_status(self, job_id: str, endpoint: str, interval: float | None = None):
        """Poll job status periodically and update chat UI when it completes."""
        try:
            import asyncio as _asyncio
            job_db = get_job_db()
            poll_interval = interval if interval is not None else getattr(self.config, 'POLL_INTERVAL', 5.0)
            while True:
                await _asyncio.sleep(poll_interval)
                job = await job_db.get_job_by_uid(job_id)
                if not job:
                    return
                status = getattr(job, 'status', None)
                if status == 'Completed' or status == JobStatus.COMPLETED:
                    try:
                        await show_results(self.chat_container, job.response, job_id)
                    except Exception as e:
                        logger.warning("Failed to render job results on poll for %s: %s", job_id, e)
                    return
                if status == 'Failed' or status == JobStatus.FAILED:
                    from frontend.pages.chatbot.chatbot_message import ChatMessage
                    self._add_message(ChatMessage('assistant', f"❌ Job {job_id} failed."))
                    return
        except Exception as e:
            logger.debug("Polling job status failed for %s: %s", job_id, e)
        except Exception as e:
            logger.debug("Error reloading recent job into chat: %s", e)
    
    async def load_and_show_form(self, endpoint: str, arguments: dict, remaining_calls: Optional[list] = None, container=None):
        """
        Load task schema and show form.
        
        Delegates to chatbot_forms.load_and_show_form for form loading and display.
        
        Args:
            endpoint (str): API endpoint name
            arguments (dict): Tool call arguments to pre-fill form
            remaining_calls (Optional[list]): Remaining tool calls in multi-call sequence
        
        Returns:
            None
        
        Tips:
        - Arguments are normalized and converted to form initial values
        - Tool selection message informs user which tool was selected
        - Form submission triggers handle_form_submit callback
        - If remaining_calls is provided, form submission will continue with next call
        """
        logger.info("Loading form for endpoint: %s", endpoint)
        logger.debug("Form arguments: %s", arguments)
        if remaining_calls:
            logger.info("Multi-call sequence: %d remaining call(s) after this one", len(remaining_calls))
        
        try:
            async def form_submit_handler(request_body, ep, ts):
                await self.form_handler.submit_form(
                    request_body, ep, ts, self.chat_container, self.core, remaining_calls
                )

            use_container = container or self.chat_container
            logger.debug("load_and_show_form wrapper: endpoint=%s use_container=%r arguments=%s", endpoint, use_container, arguments)
            await load_and_show_form(
                container=use_container,
                core=self.core,
                endpoint=endpoint,
                arguments=arguments,
                on_form_submit=form_submit_handler
            )
            logger.info("Form loaded and displayed for endpoint: %s", endpoint)
        except Exception as e:
            logger.error("Failed to load form for endpoint %s: %s", endpoint, str(e))
            await self._show_error(f'Failed to load form: {str(e)}')
    
    def _add_message(self, message: ChatMessage):
        """
        Add a message to the chat using the state manager.

        Args:
            message: ChatMessage to add
        """
        self.state_manager.add_message(message)
        # Render the message in the UI
        render_message(self.chat_container, message)
        # Trigger scroll to ensure new message is visible
        ui.timer(0.1, self.scroll_to_bottom, once=True)

    async def _show_error(self, error_message: str):
        """
        Show an error message.

        Args:
            error_message: Error message to display
        """
        show_error_message(self.chat_container, error_message)

    def _update_status(self, status: str):
        """
        Update the status text.

        Args:
            status: Status text to display
        """
        self.state_manager.set_status(status)
        # Trigger a scroll whenever status changes, as it often accompanies UI updates
        ui.timer(0.1, self.scroll_to_bottom, once=True)


    async def _handle_new_conversation(self):
        """Handle new conversation request."""
        self.state_manager.reset_conversation()
        # Clear chat container and show welcome message
        self.chat_container.clear()
        welcome_message = ChatMessage('assistant', 'New conversation started. How can I help you?')
        self._add_message(welcome_message)
        #await self.scroll_to_bottom()




@ui.page('/chatbot')
async def chatbot_page(
    load_conversation: Optional[str] = None,
    rerun: Optional[str] = None,
):
    """
    Page route handler for /chatbot.

    Query params load_conversation and rerun are passed by NiceGUI from the URL.
    Creates the chatbot page with navigation bar and renders the ChatbotPage.
    Handles URL parameters and conversation loading through the UrlParameterManager.

    Returns:
        None: Page is rendered directly
    """
    logger.info("Chatbot page route accessed (load_conversation=%s, rerun=%s)", load_conversation, rerun)

    # Import URL parameter manager
    from frontend.pages.chatbot.parameter_handlers import url_parameter_manager

    # Apply theme and create navigation
    from frontend.utils.theme import apply_saved_theme
    apply_saved_theme()
    create_navbar()
    
    # Inject global CSS to shrink the navbar and general UI elements
    ui.add_head_html('''
        <style>
            .q-header { min-height: 16px !important; }
            .q-toolbar { min-height: 16px !important; padding: 0 8px !important; }
            .q-toolbar__title { font-size: 0.85rem !important; min-height: unset !important; line-height: 32px !important; }
            .q-btn { font-size: 0.7rem !important; padding: 2px 6px !important; min-height: unset !important; }
            body { font-size: 0.8rem !important; }
            .q-textarea .q-field__control { min-height: 32px !important; }
            .q-textarea .q-field__native { padding: 4px 8px !important; line-height: 1.2 !important; min-height: 32px !important; }
        </style>
    ''')

    # Create and render chatbot
    chatbot = ChatbotPage()
    await chatbot.render()
    # Ensure global chat container is available to other helpers so selection messages
    # render into the main chat area even when callers pass input-area containers.
    try:
        from frontend.pages.chatbot.chatbot_forms import set_global_chat_container
        set_global_chat_container(chatbot.chat_container)
    except Exception:
        pass

    # Handle URL parameters (rerun, load_conversation) - prefer page params from NiceGUI
    await url_parameter_manager.detect_and_handle_url_parameters(
        chatbot, load_conversation=load_conversation, rerun=rerun
    )

    # Handle conversation loading from client storage (fallback for non-URL flows)
    await url_parameter_manager.handle_stored_conversation_loading(chatbot)

    # Ensure UI is scrolled to bottom on initial load.
    # We use a timer to catch any late-rendering components or mode switches
    # that might happen shortly after the page is loaded.
    #ui.timer(1.0, chatbot.scroll_to_bottom, once=True)

    logger.debug("Chatbot page route completed")
