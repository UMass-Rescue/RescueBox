"""
Message Processor

This module provides the MessageProcessor class for handling message sending
and processing in the chatbot interface.
"""

import logging
from typing import Optional, Dict, Any, Callable
from frontend.chatbot.message_handler import MessageHandler
from frontend.database.chat_history_db import get_chat_history_db
from frontend.pages.chatbot.chatbot_message import ChatMessage

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MessageProcessor:
    """
    Handles message sending and processing for the chatbot.

    This class encapsulates all message-related operations including sending,
    processing, and history management.
    """

    def __init__(self, state_manager, message_handler: MessageHandler):
        """
        Initialize the message processor.

        Args:
            state_manager: ChatbotStateManager instance
            message_handler: MessageHandler instance for processing messages
        """
        self.state_manager = state_manager
        self.message_handler = message_handler

        logger.debug("MessageProcessor initialized")

    def get_processing_status(self) -> bool:
        """
        Get the current processing status.

        Returns:
            bool: Whether a message is currently being processed
        """
        return self.state_manager.is_processing

    async def send_message(self,
                          message_text: str,
                          add_message_callback: Callable,
                          process_result_callback: Callable,
                          show_error_callback: Callable,
                          update_status_callback: Callable) -> Optional[Dict[str, Any]]:
        """
        Send a message and handle the complete flow.

        Args:
            message_text: The message text to send
            add_message_callback: Function to add messages to chat
            process_result_callback: Function to process handler results
            show_error_callback: Function to show errors
            update_status_callback: Function to update status

        Returns:
            Optional[Dict[str, Any]]: The handler result, or None if failed
        """
        try:
            # Set processing state
            self.state_manager.set_processing(True)
            update_status_callback("Processing message...")
            # Disable input field to prevent further input while processing
            try:
                if getattr(self.state_manager, 'input_field', None):
                    self.state_manager.input_field.disable()
            except Exception:
                logger.debug("Could not disable input field (maybe not set)")

            # Create and add user message
            user_message = ChatMessage('user', message_text)
            add_message_callback(user_message)

            # Save to history if conversation exists
            if self.state_manager.conversation_id:
                chat_history = get_chat_history_db()
                await chat_history.add_message(
                    conversation_id=self.state_manager.conversation_id,
                    role='user',
                    content=message_text
                )

            # Process the message
            logger.info("Processing message: %s", message_text[:50])
            result = await self.message_handler.handle_message(message_text, update_status_callback)

            # Handle simple message results directly (like rejection messages)
            if result and result.get('type') == 'message':
                content = result.get('content', '')
                message = ChatMessage('assistant', content)
                add_message_callback(message)
                logger.info("Handled message result directly: %s", content[:50])

                # Clear input
                self.state_manager.clear_input()

                # Brief delay to show processing completion with spinner visible
                import asyncio
                await asyncio.sleep(0.5)

                # Then reset processing state and update status
                self.state_manager.set_processing(False)
                try:
                    if getattr(self.state_manager, 'input_field', None):
                        self.state_manager.input_field.enable()
                except Exception:
                    logger.debug("Could not enable input field after processing")
                update_status_callback("✅ Rescuebox waiting for user..")
                return None  # Don't process this result further

            elif result:
                # Process complex results through the result processor
                await process_result_callback(result)
                # Ensure input is cleared and processing state reset for non-'message' results
                try:
                    self.state_manager.clear_input()
                    self.state_manager.set_processing(False)
                    try:
                        if getattr(self.state_manager, 'input_field', None):
                            self.state_manager.input_field.enable()
                    except Exception:
                        logger.debug("Could not enable input field after processing")
                    update_status_callback("✅ Rescuebox waiting for user..")
                except Exception:
                    # Best-effort; don't raise UI errors here
                    logger.debug("Failed to clear input or reset processing state after result handling")
                return None  # Don't return result to coordinator (already processed)

            # Clear input and reset processing state for flows that didn't return a 'result'
            self.state_manager.clear_input()
            self.state_manager.set_processing(False)
            try:
                if getattr(self.state_manager, 'input_field', None):
                    self.state_manager.input_field.enable()
            except Exception:
                logger.debug("Could not enable input field after processing")

            update_status_callback("✅ Rescuebox waiting for user..")
            logger.info("Message processing completed")
            return result

        except Exception as e:
            logger.error("Error sending message: %s", str(e))
            self.state_manager.set_processing(False)
            show_error_callback(f"Failed to send message: {str(e)}")
            return None
