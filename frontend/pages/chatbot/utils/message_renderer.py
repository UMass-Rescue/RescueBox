"""
Message Renderer

Handles rendering of different message types in the chat interface.
"""

import logging
from frontend.pages.chatbot.utils.message_service import MessageService


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class MessageRenderer:
    """Handles rendering of different message types in the chat interface."""

    def __init__(self, chatbot_page):
        """
        Initialize message renderer.

        Args:
            chatbot_page: ChatbotPage instance for accessing UI and callbacks
        """
        self.chatbot_page = chatbot_page
        self.logger = logging.getLogger(__name__)

    async def render_message_by_type(self, msg_record, index: int, all_messages: list):
        """
        Render message based on its type using MessageService.

        Args:
            msg_record: ChatMessageRecord instance
            index: Message index
            all_messages: All messages for context
        """
        message_type = MessageService.get_message_type(msg_record)

        if message_type == 'tool_call' and hasattr(msg_record, 'tool_calls') and msg_record.tool_calls:
            # Render tool_call and its immediate result inline if present.
            # Return True to indicate the next message was consumed (tool_result).
            consumed = await self._render_tool_call_with_context(msg_record, index, all_messages)
            return consumed
        elif message_type == 'tool_result':
            if not self._is_result_already_shown(msg_record, index, all_messages):
                MessageService.render_message_in_chat(
                    container=self.chatbot_page.chat_container,
                    message=self._create_chat_message(msg_record),
                    message_type='tool_result'
                )
        elif message_type == 'error':
            MessageService.render_message_in_chat(
                container=self.chatbot_page.chat_container,
                message=self._create_chat_message(msg_record),
                message_type='error'
            )
            return False
        else:
            # Regular text message
            MessageService.render_message_in_chat(
                container=self.chatbot_page.chat_container,
                message=self._create_chat_message(msg_record),
                message_type='text'
            )
            return False

    async def _render_tool_call_with_context(self, msg_record, index: int, all_messages: list):
        """
        Render tool call with context (checking for associated result).

        Args:
            msg_record: Tool call message record
            index: Message index
            all_messages: All messages
        """
        tool_call = msg_record.tool_calls[0] if msg_record.tool_calls else {}
        endpoint = tool_call.get('name', 'unknown')
        arguments = tool_call.get('arguments', {})

        # Check if next message is a result for this tool call
        result_content = None
        if index + 1 < len(all_messages):
            next_msg = all_messages[index + 1]
            if isinstance(next_msg, dict):
                next_type = next_msg.get('message_type', 'unknown')
                if next_type == 'tool_result':
                    result_content = next_msg.get('content', '')
            else:
                next_type = getattr(next_msg, 'message_type', 'unknown')
                if next_type == 'tool_result':
                    result_content = getattr(next_msg, 'content', '')

        # Render tool call with optional result
        logger.debug("_render_tool_call_with_context: index=%s endpoint=%s result_present=%s container=%r", index, endpoint, bool(result_content), self.chatbot_page.chat_container)
        MessageService.render_message_in_chat(
            container=self.chatbot_page.chat_container,
            message=self._create_chat_message(msg_record),
            message_type='tool_call',
            tool_calls=msg_record.tool_calls,
            endpoint=endpoint,
            arguments=arguments,
            result_content=result_content,
            on_rerun_tool=self.chatbot_page._re_run_tool
        )

        # If we rendered an inline result, indicate that the next message (tool_result) is consumed.
        logger.debug("_render_tool_call_with_context consumed=%s index=%s", bool(result_content), index)
        return bool(result_content)

    def _is_result_already_shown(self, msg_record, index: int, all_messages: list) -> bool:
        """
        Check if this tool result was already shown with the previous tool call.

        Args:
            msg_record: Current message record
            index: Current message index
            all_messages: All messages

        Returns:
            bool: True if result was already displayed
        """
        if index > 0:
            prev_msg = all_messages[index - 1]
            if isinstance(prev_msg, dict):
                prev_type = prev_msg.get('message_type', 'unknown')
                return prev_type == 'tool_call'
            else:
                prev_type = getattr(prev_msg, 'message_type', 'unknown')
                return prev_type == 'tool_call'
        return False

    def _create_chat_message(self, msg_record):
        """
        Create a ChatMessage from a message record.

        Args:
            msg_record: Message record

        Returns:
            ChatMessage: Created chat message
        """
        return MessageService.create_chat_message_from_record(msg_record)

    def create_chat_message(self, msg_record):
        """
        Public wrapper to create a ChatMessage from a message record.

        This method exists to provide a public API for other modules to
        create ChatMessage instances without accessing protected members.
        """
        return self._create_chat_message(msg_record)
