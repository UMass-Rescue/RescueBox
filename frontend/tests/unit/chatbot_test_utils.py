"""Mock factories shared by chatbot unit and integration tests."""

from unittest.mock import AsyncMock, MagicMock


class TestUtilities:
    """Lightweight utilities for chatbot smoke and integration tests."""

    @staticmethod
    def create_mock_chatbot_page() -> MagicMock:
        chatbot = MagicMock()
        chatbot.state_manager = MagicMock()
        chatbot.state_manager.conversation_id = None
        chatbot.state_manager.messages = []
        return chatbot

    @staticmethod
    def create_mock_tool_registry() -> MagicMock:
        return MagicMock()

    @staticmethod
    def create_mock_response_body() -> MagicMock:
        return MagicMock()

    @staticmethod
    def create_mock_message_handler() -> MagicMock:
        handler = MagicMock()
        handler.handle_message = AsyncMock(return_value={'type': 'message', 'content': 'ok'})
        return handler

    @staticmethod
    def create_mock_task_schema() -> MagicMock:
        return MagicMock()
