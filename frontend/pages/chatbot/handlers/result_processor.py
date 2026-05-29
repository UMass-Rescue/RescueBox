"""
Result Processor

This module provides the ResultProcessor class for processing handler results
and coordinating next actions in the chatbot interface.
"""

import logging
from typing import Dict, Any, Callable, Optional
from frontend.pages.chatbot.chatbot_forms import (
    show_tool_picker,
    show_analysis_picker,
    show_tool_selection,
    load_and_show_form
)
from frontend.chatbot.config import ToolRegistry
# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ResultProcessor:
    """
    Processes handler results and coordinates next actions.

    This class handles the different types of results from message processing
    and orchestrates the appropriate UI responses.
    """

    def __init__(self, state_manager, tool_registry: ToolRegistry):
        """
        Initialize the result processor.

        Args:
            state_manager: ChatbotStateManager instance
            tool_registry: ToolRegistry instance
        """
        self.state_manager = state_manager
        self.tool_registry = tool_registry

        logger.debug("ResultProcessor initialized")

    async def process_result(self,
                           result: Dict[str, Any],
                           container,
                           core,
                           add_message_callback: Callable,
                           show_error_callback: Callable,
                           update_status_callback: Callable,
                           load_form_callback: Callable = None,
                           set_input_enabled_callback: Callable = None):
        """
        Process a handler result and trigger appropriate actions.

        Args:
            result: Result dictionary from message handler
            container: UI container for displaying content
            core: ChatbotCore instance
            add_message_callback: Function to add messages
            show_error_callback: Function to show errors
            update_status_callback: Function to update status
            load_form_callback: Function to load forms
        """
        logger.debug("ResultProcessor.process_result called with result type: %s", result.get('type', 'unknown'))
        result_type = result.get('type', 'unknown')
        logger.debug("Processing result type: %s", result_type)

        def _set_input(enabled: bool):
            if set_input_enabled_callback:
                try:
                    set_input_enabled_callback(enabled)
                except Exception:
                    pass

        try:
            if result_type == 'show_form':
                _set_input(False)
                await self._handle_show_form(result, container, core, load_form_callback)
                # Scroll + "Fill the form…" status come from MessageProcessor once (avoids duplicate
                # scroll_form_into_view_with_retries fighting each other).
                update_status_callback("Ready", scroll_after=False)
                return

            elif result_type == 'multi_tool_calls':
                _set_input(False)
                await self._handle_multi_tool_calls(result, container, load_form_callback, add_message_callback)
                return

            elif result_type == 'message':
                _set_input(True)
                logger.debug("About to call _handle_message for result: %s", result)
                await self._handle_message(result, add_message_callback)
                logger.debug("_handle_message completed")

            elif result_type == 'error':
                _set_input(True)
                await self._handle_error(result, show_error_callback)

            elif result_type == 'help':
                _set_input(True)
                await self._handle_help(result, add_message_callback)

            elif result_type == 'tool_picker':
                _set_input(False)
                await self._handle_tool_picker(result, container, add_message_callback)
                update_status_callback("Ready", scroll_after=False)
                return

            elif result_type == 'analysis_picker':
                _set_input(False)
                await self._handle_analysis_picker(result, container, add_message_callback)
                update_status_callback("Ready", scroll_after=False)
                return

            else:
                _set_input(True)
                logger.warning("Unknown result type: %s", result_type)
                show_error_callback(f"Unknown response type: {result_type}")

            update_status_callback("Ready", scroll_to_form=False)

        except Exception as e:
            logger.error("Error processing result: %s", str(e))
            show_error_callback(f"Error processing response: {str(e)}")

    async def _handle_show_form(self, result: Dict[str, Any], container, core, load_form_callback):
        """Handle show_form result type."""
        endpoint = result.get('endpoint')
        arguments = result.get('arguments', {})

        if load_form_callback:
            await load_form_callback(endpoint, arguments)
        else:
            # Fallback to direct form loading (rare - load_form_callback usually set)
            def _on_cancel():
                if self.state_manager:
                    try:
                        self.state_manager.set_input_enabled(True)
                    except Exception:
                        pass

            await load_and_show_form(
                container=container,
                core=core,
                endpoint=endpoint,
                arguments=arguments,
                on_form_submit=self._create_form_submit_handler(container, core),
                on_form_cancel=_on_cancel
            )

    async def _handle_multi_tool_calls(self, result: Dict[str, Any], container, load_form_callback, add_message_callback):
        """Handle multi_tool_calls result type."""
        from frontend.components.shared.notifications import notify_info

        tool_calls = result.get('tool_calls', [])
        notify_info(
            f"Processing {len(tool_calls)} tool call(s) sequentially...",
        )

        # Create a proper ChatMessage object
        #from frontend.pages.chatbot.chatbot_message import ChatMessage
        #message = ChatMessage('assistant',
        #    f"Processing {len(tool_calls)} task(s) sequentially:\n" +
        #    "\n".join([f"{i+1}. {call['endpoint']}" for i, call in enumerate(tool_calls)])
        #)
        # Do not scroll to bottom here: scroll_to_bottom retries (~700ms) override form scrollIntoView.
        #add_message_callback(message, False)

        # Start with first tool call
        if tool_calls and load_form_callback:
            first_call = tool_calls[0]
            await load_form_callback(
                first_call['endpoint'],
                first_call['arguments'],
                remaining_calls=tool_calls[1:] if len(tool_calls) > 1 else None
            )
            # Form scroll is scheduled once from MessageProcessor (update_status … scroll_to_form=True).

    async def _handle_message(self, result: Dict[str, Any], add_message_callback):
        """Handle message result type."""
        content = result.get('content', '')
        logger.debug("Handling message result with content: %s", content[:50])
        # Create a proper ChatMessage object
        from frontend.pages.chatbot.chatbot_message import ChatMessage
        message = ChatMessage('assistant', content)
        logger.debug("Created ChatMessage: role=%s, content_length=%d", message.role, len(message.content))
        add_message_callback(message)
        logger.debug("Called add_message_callback for rejection message")

    async def _handle_error(self, result: Dict[str, Any], show_error_callback):
        """Handle error result type."""
        content = result.get('content', 'Unknown error')
        show_error_callback(content)

    async def _handle_help(self, result: Dict[str, Any], add_message_callback):
        """Handle help result type by showing a dedicated dialog."""
        content = result.get('content', 'No help available')
        try:
            # Import lazily to avoid circular imports during startup/tests
            from frontend.components.chat.help_dialog import show_help_dialog
            show_help_dialog(content, title="RescueBox Model Assistant Help")
        except Exception as e:
            logger.exception("Failed to show help dialog, falling back to inline message: %s", e)
            from frontend.pages.chatbot.chatbot_message import ChatMessage
            message = ChatMessage('assistant', content)
            add_message_callback(message)

    async def _handle_tool_picker(self, result: Dict[str, Any], container, add_message_callback):
        """Handle tool_picker result type."""
        # Clear container and show tool picker menu
        container.clear()
        await show_tool_picker(
            container=container,
            tool_registry=self.tool_registry,
            on_tool_selected=self._create_tool_selected_handler(container, add_message_callback)
        )

    async def _handle_analysis_picker(self, _result: Dict[str, Any], container, add_message_callback):
        """Handle analysis_picker result type."""
        # Clear container and show analysis picker menu
        container.clear()
        await show_analysis_picker(
            container=container,
            on_analysis_selected=self._create_analysis_selected_handler(container, add_message_callback)
        )

    def _create_form_submit_handler(self, container, core):
        """Create a form submit handler function."""
        async def form_submit_handler(request_body, endpoint, task_schema):
            # Import here to avoid circular imports
            from frontend.pages.chatbot.handlers.form_submit_handler import FormSubmitHandler
            handler = FormSubmitHandler(self.state_manager)
            return await handler.submit_form(request_body, endpoint, task_schema, container, core)
        return form_submit_handler

    def _create_tool_selected_handler(self, container, add_message_callback):
        """Create a tool selected handler function."""
        async def tool_selected_handler(endpoint, arguments):
            # Show the in-UI tool selection message, but do not persist to chat history yet.
            # Persisting the assistant 'Selected tool' message immediately caused leftover
            # history entries when a user cancelled the input form, so we avoid adding it
            # to the conversation here. The form submit flow should add a proper history
            # entry when the job is submitted.
            await show_tool_selection(container, endpoint)
        return tool_selected_handler

    def _create_analysis_selected_handler(self, container, add_message_callback):
        """Create an analysis selected handler function."""
        async def analysis_selected_handler(analysis_type):
            from frontend.pages.chatbot.chatbot_message import ChatMessage
            message = ChatMessage('assistant', f"Selected analysis: {analysis_type}")
            add_message_callback(message)
            # Note: This would typically trigger appropriate analysis workflow
        return analysis_selected_handler

    def get_result_types(self) -> list:
        """
        Get the list of supported result types.

        Returns:
            list: Supported result types
        """
        return ['show_form', 'multi_tool_calls', 'message', 'error', 'help', 'tool_picker', 'analysis_picker']
