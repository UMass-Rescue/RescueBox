"""
Conversation Loader.

Handles conversation loading and message processing operations.
"""

import logging
from nicegui import ui
from frontend.pages.chatbot.utils.message_renderer import MessageRenderer
from frontend.database.chat_history_db import ChatMessageRecord


class ConversationLoader:
    """Handles conversation loading and message processing operations."""

    def __init__(self, chatbot_page):
        """
        Initialize conversation loader with chatbot page reference.

        Args:
            chatbot_page: Reference to ChatbotPage instance
        """
        self.chatbot_page = chatbot_page
        self.logger = logging.getLogger(__name__)
        self.message_renderer = MessageRenderer(chatbot_page)

    async def load_conversation(self, conversation_data: dict):
        """
        Append a historical conversation to the current chat.

        Args:
            conversation_data: Dictionary containing conversation_id, conversation_data, and messages
        """
        self.logger.debug("Appending historical conversation to current chat: %s", conversation_data)

        try:
            # Extract conversation components
            conversation_id, conversation, messages = self._extract_conversation_data(conversation_data)

            # Prepare the chat interface for appending
            self._prepare_chat_interface(conversation_id, conversation)

            # Append all historical messages
            await self._load_all_messages(messages)

            # Disable input: loaded conversation is view-only (read, review, re-run).
            # User must start New Conversation to type a new prompt.
            try:
                self.chatbot_page.state_manager.set_input_enabled(False)
                self.chatbot_page.state_manager.set_status(
                    "View previous chat, re-run model or start a new conversation"
                )
            except Exception as e:
                self.logger.debug("Could not disable input after load: %s", e)

            self.logger.debug("Historical conversation appended successfully: %s", conversation_id)

        except KeyError as e:
            # Handle missing required data gracefully
            self.logger.warning("Missing required conversation data: %s", str(e))
            return  # Don't raise, just return
        except Exception as e:
            self.logger.error("Error appending historical conversation: %s", str(e))
            raise

    def _extract_conversation_data(self, conversation_data: dict) -> tuple:
        """
        Extract conversation components from data dictionary.

        Returns:
            tuple: (conversation_id, conversation, messages)
        """
        conversation_id = conversation_data['conversation_id']
        conversation = conversation_data['conversation_data']
        messages = conversation_data['messages']

        # Handle conversation data (could be dict or ConversationRecord)
        if isinstance(conversation, dict):
            conversation_title = conversation.get('title', 'unknown')
        else:
            conversation_title = getattr(conversation, 'title', 'unknown')

        self.logger.debug("Extracted conversation: %s (%d messages)", conversation_id, len(messages))
        self.logger.debug("Conversation title: %s", conversation_title)

        return conversation_id, conversation, messages

    def _prepare_chat_interface(self, conversation_id: str, conversation):
        """
        Prepare the chat interface for appending historical conversation.

        Args:
            conversation_id: The conversation ID to load
            conversation: Conversation data (dict or object)
        """
        self.logger.debug("Preparing chat interface for appending conversation: %s", conversation_id)

        # Set the conversation ID in the state manager
        self.chatbot_page.state_manager.set_conversation_id(conversation_id)

        # Note: Keep existing conversation state and container content
        # Don't reset conversation or clear container - just append history
        self.logger.debug("Keeping existing chat content and appending history")

    async def _load_all_messages(self, messages: list):
        """
        Load all messages in the conversation, appending to existing content.

        Args:
            messages: List of message dictionaries or objects
        """
        self.logger.debug("Appending %d historical messages to current chat", len(messages))

        # Add a visual separator for historical content
        if hasattr(self.chatbot_page, 'chat_container') and messages:
            with self.chatbot_page.chat_container:
                ui.separator()
                ui.label('Conversation history').classes(
                    'text-xs font-medium text-zinc-500 uppercase tracking-wide'
                )

        i = 0
        while i < len(messages):
            try:
                consumed_next = await self._load_single_message(messages[i], i, messages)
                if consumed_next:
                    # Skip the next message because it was rendered inline as a result
                    i += 2
                else:
                    i += 1
            except Exception as e:
                self.logger.warning("Failed to load historical message %d: %s", i+1, str(e))
                i += 1

    async def _load_single_message(self, msg_dict, index: int, all_messages: list):
        """
        Load a single message with appropriate rendering.

        Args:
            msg_dict: Message data (dict or object)
            index: Message index in the list
            all_messages: Complete list of messages for context
        """
        # Get message details for logging
        role, msg_type, content = self._get_message_details(msg_dict)
        self.logger.debug("Loading message %d/%d: role=%s, type=%s, content=%s",
                         index+1, len(all_messages), role, msg_type, content[:50])

        # Convert to ChatMessageRecord if needed
        msg_record = self._convert_to_record(msg_dict)

        # Add to state manager for conversation history using public API
        chat_message = self.message_renderer.create_chat_message(msg_record)
        self.chatbot_page.state_manager.add_message(chat_message)

        # Render the message based on its type; renderer may consume the next message (tool_result)
        consumed = await self.message_renderer.render_message_by_type(msg_record, index, all_messages)
        return bool(consumed)

    def _get_message_details(self, msg_dict) -> tuple:
        """
        Extract basic message details for logging.

        Returns:
            tuple: (role, message_type, content)
        """
        if isinstance(msg_dict, dict):
            role = msg_dict.get('role', 'unknown')
            msg_type = msg_dict.get('message_type', 'unknown')
            content = msg_dict.get('content', '')[:50]
        else:
            role = getattr(msg_dict, 'role', 'unknown')
            msg_type = getattr(msg_dict, 'message_type', 'unknown')
            content = getattr(msg_dict, 'content', '')[:50]

        return role, msg_type, content

    def _convert_to_record(self, msg_dict):
        """
        Convert message dict to ChatMessageRecord if needed.

        Args:
            msg_dict: Message data

        Returns:
            ChatMessageRecord: Converted message record
        """
        if isinstance(msg_dict, dict):
            return ChatMessageRecord(**msg_dict)
        return msg_dict

