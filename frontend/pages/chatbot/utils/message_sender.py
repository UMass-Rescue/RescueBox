"""
Message Sender

Handles the complete message sending workflow.
"""

import logging
from typing import Optional, Dict, Any

from frontend.pages.chatbot.utils.database_service import DatabaseService


class MessageSender:
    """Handles the complete message sending workflow."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def send_message(self,
                          message_text: str,
                          input_field,
                          is_processing_ref: dict,
                          message_handler,
                          process_handler_result_func,
                          add_message_func,
                          show_error_func,
                          update_status_func,
                          conversation_id_ref: Optional[dict] = None):
        """
        Send a user message through the complete workflow.

        Args:
            message_text: The message text to send
            input_field: The input field widget
            is_processing_ref: Dict with processing state
            message_handler: MessageHandler instance
            process_handler_result_func: Function to process results
            add_message_func: Function to add messages to chat
            show_error_func: Function to show errors
            update_status_func: Function to update status
            conversation_id_ref: Optional conversation ID reference

        Returns:
            None
        """
        if not message_text.strip() or is_processing_ref.get('value', False):
            return

        try:
            # Setup conversation if needed
            conversation_id = await self._setup_conversation(conversation_id_ref)

            # Save user message to chat history
            await self._save_user_message(conversation_id, message_text)

            # Update UI for processing
            await self._update_ui_for_processing(
                message_text, input_field, is_processing_ref,
                add_message_func, update_status_func
            )

            # Process the message
            result = await message_handler.handle_message(message_text, conversation_id)

            # Save assistant response to chat history
            await self._save_assistant_response(conversation_id, result)

            # Process the result
            await process_handler_result_func(result, input_field, is_processing_ref)

        except Exception as e:
            self.logger.error("Message sending failed: %s", str(e))
            await show_error_func(f"Failed to send message: {str(e)}")

    async def _setup_conversation(self, conversation_id_ref: Optional[dict]) -> Optional[str]:
        """Setup or get existing conversation ID."""
        if conversation_id_ref:
            return conversation_id_ref.get('value')
        return None

    async def _save_user_message(self, conversation_id: Optional[str], message_text: str):
        """Save user message to chat history."""
        if conversation_id:
            try:
                await DatabaseService.save_message_to_history(
                    conversation_id=conversation_id,
                    role='user',
                    content=message_text,
                    message_type='text'
                )
                self.logger.debug("Saved user message to conversation %s", conversation_id)
            except Exception as e:
                self.logger.warning("Failed to save user message to chat history: %s", str(e))

    async def _update_ui_for_processing(self, message_text: str, input_field, is_processing_ref: dict,
                                       add_message_func, update_status_func):
        """Update UI state for processing."""
        # Mark as processing
        is_processing_ref['value'] = True

        # Clear input field
        input_field.value = ''

        # Add user message to chat
        await add_message_func(message_text, 'user')

        # Update status
        await update_status_func("Processing...")

    async def _save_assistant_response(self, conversation_id: Optional[str], result: dict):
        """Save assistant response to chat history."""
        if conversation_id:
            try:
                content = result.get('content', '') if isinstance(result, dict) else str(result)
                await DatabaseService.save_message_to_history(
                    conversation_id=conversation_id,
                    role='assistant',
                    content=content,
                    message_type='text'
                )
                self.logger.debug("Saved assistant response to conversation %s", conversation_id)
            except Exception as e:
                self.logger.warning("Failed to save assistant response to chat history: %s", str(e))
