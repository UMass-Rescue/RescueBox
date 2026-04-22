"""
Message Flow Coordinator

This module provides the MessageFlowCoordinator class that unifies all message
processing, result routing, and form submission logic into a single, coordinated
interface for the chatbot.
"""

import logging
from typing import Dict, Any, Callable, Optional
from nicegui import ui
from frontend.chatbot.config import ToolRegistry
from frontend.chatbot.core import ChatbotCore
from frontend.pages.chatbot.state import ChatbotStateManager
from frontend.pages.chatbot.handlers.message_processor import MessageProcessor
from frontend.pages.chatbot.handlers.result_processor import ResultProcessor
from frontend.pages.chatbot.handlers.form_submit_handler import FormSubmitHandler

logger = logging.getLogger(__name__)


class MessageFlowCoordinator:
    """
    Unified coordinator for all chatbot message processing workflows.

    This class provides a single entry point for handling the complete message
    flow from user input through processing, form display, submission, and
    result presentation. It coordinates multiple specialized handlers to
    provide a seamless user experience.
    """

    def __init__(self, state_manager: ChatbotStateManager, form_loader: Optional[Callable] = None):
        """
        Initialize the message flow coordinator.

        Args:
            state_manager: The chatbot state manager
            form_loader: Optional function to load and display forms
        """
        self.state_manager = state_manager
        self.form_loader = form_loader
        self.logger = logging.getLogger(__name__)

        # Initialize specialized handlers
        self.message_processor = MessageProcessor(state_manager, None)  # Will be set later
        self.result_processor = ResultProcessor(state_manager, None)  # tool_registry will be set later
        self.form_submit_handler = FormSubmitHandler(state_manager)

        # Store state manager for later use
        self._state_manager = state_manager

        self.logger.debug("MessageFlowCoordinator initialized")

    def set_message_handler(self, message_handler):
        """Set the message handler for the message processor."""
        self.message_processor.message_handler = message_handler

    def set_tool_registry(self, tool_registry):
        """Set the tool registry for the result processor."""
        self.result_processor.tool_registry = tool_registry

    async def process_user_message(
        self,
        message_text: str,
        input_field: ui.textarea,
        is_processing_ref: dict,
        add_message_func: Callable,
        show_error_func: Callable,
        update_status_func: Callable,
        core: Optional[Any] = None
    ) -> None:
        """
        Process a complete user message flow from input to result.


        This is the main entry point for handling user messages. It coordinates
        the message processing, result routing, and any subsequent form handling.

        Args:
            message_text: The user's message text
            input_field: The UI input field
            is_processing_ref: Reference to processing state
            add_message_func: Function to add messages to chat
            show_error_func: Function to show errors
            update_status_func: Function to update status
            core: Optional ChatbotCore instance for result processing
        """
        try:
            self.logger.debug("Starting user message processing flow")

            # Step 1: Process the message through the message handler
            result = await self.message_processor.send_message(
                message_text=message_text,
                add_message_callback=add_message_func,
                process_result_callback=self._create_result_processor(input_field, is_processing_ref, add_message_func, show_error_func, update_status_func, core),
                show_error_callback=show_error_func,
                update_status_callback=update_status_func
            )

            if result:
                # Step 2: Route the result to appropriate action
                await self._route_message_result(
                    result=result,
                    input_field=input_field,
                    is_processing_ref=is_processing_ref,
                    add_message_func=add_message_func,
                    show_error_func=show_error_func,
                    update_status_func=update_status_func
                )

        except Exception as e:
            self.logger.error("Error in message processing flow: %s", str(e))
            await show_error_func(f"Message processing failed: {str(e)}")

    def _create_result_processor(self, input_field: ui.textarea, is_processing_ref: dict, add_message_func: Callable, show_error_func: Callable, update_status_func: Callable, core):
        """
        Create a result processor callback for message handling.

        Args:
            input_field: The UI input field
            is_processing_ref: Reference to processing state
            add_message_func: Function to add messages to chat
            show_error_func: Function to show errors
            update_status_func: Function to update status
            core: ChatbotCore instance for result processing

        Returns:
            Callable that handles message processing results
        """
        async def process_result(result: Dict[str, Any]) -> None:
            # Route the result first
            await self._route_message_result(
                result=result,
                input_field=input_field,
                is_processing_ref=is_processing_ref,
                add_message_func=add_message_func,
                show_error_func=show_error_func,
                update_status_func=update_status_func,
                core=core
            )

            # Update processing state after routing completes.
            # Input enable/disable is handled by message_processor based on result type
            # (rule: enabled only when no pending chat interaction).
            is_processing_ref['value'] = False
            self.state_manager.set_processing(False)

        return process_result

    async def _route_message_result(
        self,
        result: Dict[str, Any],
        input_field: ui.textarea,
        is_processing_ref: dict,
        add_message_func: Callable,
        show_error_func: Callable,
        update_status_func: Callable,
        core = None
    ) -> None:
        """
        Route message processing results to appropriate handlers.

        Args:
            result: The result from message processing
            input_field: The UI input field
            is_processing_ref: Reference to processing state
            add_message_func: Function to add messages to chat
            show_error_func: Function to show errors
            update_status_func: Function to update status
            core: Optional ChatbotCore instance for result processing
        """
        result_type = result.get('type', 'unknown')
        self.logger.debug("Routing result type: %s", result_type)

        # Create callbacks for result processor
        callbacks = self._create_result_callbacks(
            input_field=input_field,
            is_processing_ref=is_processing_ref,
            add_message_func=add_message_func,
            show_error_func=show_error_func,
            update_status_func=update_status_func
        )

        # Prefer a chat container set on the coordinator; fall back to provided input_field.
        coordinator_chat_container = getattr(self, 'chat_container', None)
        container_for_processing = coordinator_chat_container or input_field
        # Detailed diagnostic logging to trace which container is selected for rendering
        try:
            self.logger.debug(
                "Coordinator selected render container: coordinator_chat_container=%r input_field=%r chosen=%r",
                coordinator_chat_container, input_field, container_for_processing
            )
            # Log a few attributes that help identify input-area vs chat-area
            self.logger.debug(
                "Container attrs: has_input_field=%s has_client=%s",
                bool(getattr(container_for_processing, 'input_field', None)),
                bool(getattr(container_for_processing, 'client', None))
            )
        except Exception:
            # best-effort diagnostics, ignore if repr/access fails
            pass

        # Route through result processor using the chat container so forms and assistant
        # messages render in the correct conversation area.
        await self.result_processor.process_result(
            result=result,
            container=container_for_processing,
            core=core,
            **callbacks
        )

    def _create_result_callbacks(
        self,
        input_field: ui.textarea,
        is_processing_ref: dict,
        add_message_func: Callable,
        show_error_func: Callable,
        update_status_func: Callable
    ) -> Dict[str, Callable]:
        """
        Create standardized callbacks for result processing.

        Args:
            input_field: The UI input field
            is_processing_ref: Reference to processing state
            add_message_func: Function to add messages to chat
            show_error_func: Function to show errors
            update_status_func: Function to update status

        Returns:
            Dict of callback functions
        """
        def add_assistant_message_func(message, scroll_after=True):
            logger.debug("Coordinator callback called with message: role=%s, content='%s'", message.role, message.content[:50])
            try:
                add_message_func(message, scroll_after)
                logger.debug("Coordinator callback completed successfully")
            except Exception as e:
                logger.error("Error in coordinator callback: %s", str(e))

        async def load_and_show_form_func(endpoint: str, arguments: dict, remaining_calls=None):
            self.logger.debug("Loading form for endpoint: %s", endpoint)
            if self.form_loader:
                await self.form_loader(endpoint, arguments, remaining_calls)
            else:
                self.logger.warning("No form loading function provided")

        async def show_results_func(response_body, job_id=None):
            # This would integrate with result display
            self.logger.debug("Showing results for job: %s", job_id)
            # Implementation would delegate to result display logic

        return {
            'add_message_callback': add_assistant_message_func,
            'load_form_callback': load_and_show_form_func,
            'show_error_callback': show_error_func,
            'update_status_callback': update_status_func
        }

    async def submit_form(
        self,
        request_body,
        endpoint: str,
        task_schema,
        container,
        core: ChatbotCore,
        remaining_calls=None,
        conversation_id=None
    ):
        """
        Submit a form through the form submit handler.

        Args:
            request_body: The form request body
            endpoint: The API endpoint
            task_schema: The task schema
            container: The UI container
            core: The chatbot core
            remaining_calls: Any remaining chained calls
            conversation_id: The conversation ID
        """
        return await self.form_submit_handler.submit_form(
            request_body=request_body,
            endpoint=endpoint,
            task_schema=task_schema,
            container=container,
            core=core,
            remaining_calls=remaining_calls,
            conversation_id=conversation_id
        )

    async def reset_conversation(self):
        """Reset the conversation state."""
        self.state_manager.reset_conversation()
        self.logger.debug("Conversation reset through coordinator")
