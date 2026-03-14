"""
Result Router

Routes handler results to appropriate UI actions.
"""

import logging
from typing import Dict

from nicegui import ui
from frontend.pages.chatbot.chatbot_forms import show_tool_picker


class ResultRouter:
    """Routes handler results to appropriate UI actions."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def route_result(self,
                          result: Dict,
                          chat_container,
                          tool_registry,
                          add_assistant_message_func,
                          show_error_func,
                          load_and_show_form_func):
        """
        Route a handler result to the appropriate UI action.

        Args:
            result: The result dictionary from message processing
            chat_container: Container for chat messages
            tool_registry: Tool registry for available tools
            add_assistant_message_func: Function to add assistant messages
            show_error_func: Function to show errors
            load_and_show_form_func: Function to load forms

        Returns:
            None
        """
        result_type = result.get('type', 'message')

        if result_type == 'message':
            await self._route_message_result(result, add_assistant_message_func, show_error_func)
        elif result_type == 'help':
            # Handle help result, now asynchronously
            await add_assistant_message_func(result.get('content', ''))
        elif result_type == 'tool_picker':
            await self._handle_tool_picker(result, chat_container, tool_registry, load_and_show_form_func)
        elif result_type == 'show_form':
            await self._handle_show_form(result, load_and_show_form_func)
        elif result_type == 'multi_tool_calls':
            await self._handle_multi_tool_calls(result, add_assistant_message_func, load_and_show_form_func)
        elif result_type == 'error':
            await show_error_func(result.get('content', 'Unknown error'))
        else:
            self.logger.warning("Unknown result type: %s", result_type)

    async def _route_message_result(self, result: dict, add_assistant_message_func, show_error_func):
        """Route a simple message result."""
        content = result.get('content', '')
        if content:
            await add_assistant_message_func(content, 'assistant')
        else:
            await show_error_func("No response content received")

    async def _handle_tool_picker(self, result: dict, chat_container, tool_registry, load_and_show_form_func):
        """Handle tool picker result."""
        content = result.get('content', '')
        if content:
            # Add the assistant message first
            with chat_container:
                ui.chat_message(content, name='Assistant', avatar='🤖')

        # Show tool picker
        async def on_tool_selected(endpoint: str, arguments: dict):
            await load_and_show_form_func(endpoint, arguments)

        await show_tool_picker(chat_container, tool_registry, on_tool_selected)

    async def _handle_show_form(self, result: dict, load_and_show_form_func):
        """Handle show form result."""
        endpoint = result.get('endpoint', '')
        arguments = result.get('arguments', {})

        if endpoint:
            await load_and_show_form_func(endpoint, arguments)
        else:
            self.logger.error("Show form result missing endpoint")

    async def _handle_multi_tool_calls(self, result: dict, add_assistant_message_func, load_and_show_form_func):
        """Handle multiple tool calls sequentially."""
        tool_calls = result.get('tool_calls', [])
        if not tool_calls:
            self.logger.error("Multi tool calls result missing tool_calls")
            return

        # Add assistant message if present
        content = result.get('content', '')
        if content:
            await add_assistant_message_func(content, 'assistant')

        # Start with first tool call
        first_call = tool_calls[0]
        endpoint = first_call.get('endpoint', '')
        arguments = first_call.get('arguments', {})

        if endpoint:
            await load_and_show_form_func(
                endpoint,
                arguments,
                remaining_calls=tool_calls[1:] if len(tool_calls) > 1 else None
            )
