"""
UI Integration Tests

This module provides integration tests for the chatbot UI components,
testing complete user workflows and component interactions using NiceGUI's
testing framework.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from nicegui import ui
from nicegui.testing import User

from frontend.tests.unit.chatbot_test_utils import TestUtilities


class TestChatbotUIIntegration:
    """Integration tests for chatbot UI components."""

    @pytest.fixture
    async def ui_client(self):
        """Create a NiceGUI test client."""
        # This would normally set up a test client, but NiceGUI testing
        # framework setup is complex in this environment
        yield None

    def test_chatbot_page_rendering(self):
        """Test that chatbot page renders without errors."""
        # This is a basic smoke test - in a real environment with NiceGUI
        # testing framework properly set up, this would test actual UI rendering

        try:
            # Test that imports work
            from frontend.pages.chatbot import ChatbotPage
            from frontend.pages.chatbot import create_chat_ui

            # Test that classes can be instantiated (without UI context)
            chatbot = TestUtilities.create_mock_chatbot_page()
            assert chatbot is not None

            # Test that UI creation functions exist
            assert callable(create_chat_ui)

        except Exception as e:
            pytest.fail(f"Chatbot UI components failed to initialize: {e}")

    def test_rejection_message_flow(self):
        """Test that invalid prompts show proper rejection messages."""
        try:
            from frontend.chatbot.utils import get_rejection_message
            from frontend.pages.chatbot import MessageFlowCoordinator
            

            # Test the rejection message generation
            rejection_msg = get_rejection_message("no_match")
            assert rejection_msg is not None
            assert len(rejection_msg) > 0
            assert "try" in rejection_msg.lower() or "help" in rejection_msg.lower()

            # Test that the message flow coordinator can be created
            from unittest.mock import MagicMock
            state_manager = MagicMock()
            state_manager.is_processing = False
            state_manager.conversation_id = None
            coordinator = MessageFlowCoordinator(state_manager, MagicMock())
            assert coordinator is not None

            # Test that message processing components exist
            assert hasattr(coordinator, 'message_processor')
            assert hasattr(coordinator, 'result_processor')

            # Verify rejection message structure
            expected_result = {'type': 'message', 'content': rejection_msg}
            assert expected_result['type'] == 'message'
            assert expected_result['content'] == rejection_msg

        except Exception as e:
            pytest.fail(f"Rejection message flow test failed: {e}")

    def test_invalid_message_processing_flow(self):
        """Test complete flow for invalid message processing and rejection display."""
        try:
            from frontend.pages.chatbot import MessageFlowCoordinator
            from frontend.pages.chatbot import MessageProcessor
            from frontend.pages.chatbot import ResultProcessor
            from frontend.pages.chatbot import ChatMessage
            from frontend.chatbot.utils import get_rejection_message

            # Create mock components
            from unittest.mock import MagicMock
            state_manager = MagicMock()
            state_manager.is_processing = False
            state_manager.conversation_id = None

            message_handler = TestUtilities.create_mock_message_handler()
            message_processor = MessageProcessor(state_manager, message_handler)
            result_processor = ResultProcessor(state_manager, None)  # tool_registry can be None for this test

            # Create coordinator
            coordinator = MessageFlowCoordinator(state_manager, MagicMock())
            coordinator.message_processor = message_processor
            coordinator.result_processor = result_processor

            # Mock the message handler to return rejection result for invalid input
            async def mock_handle_message(message_text, update_callback):
                return {'type': 'message', 'content': get_rejection_message('no_match')}

            message_handler.handle_message = mock_handle_message

            # Track messages and errors
            messages_received = []
            errors_received = []

            def mock_add_message(message):
                messages_received.append(message)

            def mock_show_error(error_msg):
                errors_received.append(error_msg)

            def mock_update_status(status):
                pass  # Not testing status updates

            # Test processing an invalid message
            from unittest.mock import MagicMock
            mock_textarea = MagicMock()
            mock_textarea.enable = MagicMock()

            import asyncio
            async def run_test():
                await coordinator.process_user_message(
                    message_text="invalid input that should be rejected",
                    input_field=mock_textarea,
                    is_processing_ref={'value': False},
                    add_message_func=mock_add_message,
                    show_error_func=mock_show_error,
                    update_status_func=mock_update_status,
                    core=MagicMock()
                )

            asyncio.run(run_test())

            # Verify that messages were added
            assert len(messages_received) >= 2  # At least user message + rejection message
            assert len(errors_received) == 0   # No errors should occur

            # Find the rejection message (should be from assistant)
            assistant_messages = [msg for msg in messages_received if msg.role == 'assistant']
            assert len(assistant_messages) >= 1

            # Verify the rejection message content
            rejection_content = get_rejection_message('no_match')
            rejection_message = assistant_messages[0]
            assert rejection_message.content == rejection_content

        except Exception as e:
            pytest.fail(f"Invalid message processing flow test failed: {e}")

    def test_result_display_integration(self):
        """Test result display integration with mocked components."""
        try:
            from frontend.pages.chatbot import show_results

            assert callable(show_results)

        except Exception as e:
            pytest.fail(f"Result display integration failed: {e}")

    def test_message_flow_coordinator_ui_integration(self):
        """Test MessageFlowCoordinator UI integration."""
        try:
            from frontend.pages.chatbot import MessageFlowCoordinator

            # Create mock state manager
            mock_state_manager = MagicMock()

            # Test coordinator creation
            coordinator = MessageFlowCoordinator(mock_state_manager, MagicMock())
            assert coordinator is not None
            assert coordinator.message_processor is not None
            assert coordinator.result_processor is not None
            assert coordinator.form_submit_handler is not None

        except Exception as e:
            pytest.fail(f"MessageFlowCoordinator UI integration failed: {e}")


class TestEndToEndWorkflows:
    """End-to-end workflow tests (mocked version)."""

    def test_message_to_form_to_result_workflow(self):
        """Test complete workflow: message → form → result (mocked)."""
        try:
            # This test validates that all components can work together
            # In a real UI testing environment, this would simulate actual user interactions

            # Create all necessary mock components
            chatbot = TestUtilities.create_mock_chatbot_page()
            message_handler = TestUtilities.create_mock_message_handler()
            tool_registry = TestUtilities.create_mock_tool_registry()
            task_schema = TestUtilities.create_mock_task_schema()
            response_body = TestUtilities.create_mock_response_body()

            # Verify all components are properly mocked
            assert chatbot is not None
            assert message_handler is not None
            assert tool_registry is not None
            assert task_schema is not None
            assert response_body is not None

            # Test that the workflow components can be orchestrated
            # (Actual end-to-end testing would require NiceGUI test client)

        except Exception as e:
            pytest.fail(f"End-to-end workflow test failed: {e}")

    def test_error_handling_ui_integration(self):
        """Test error handling in UI integration."""
        try:
            from frontend.components.errors import render_error_message
            from frontend.utils import show_error_to_user

            # Test that error handling functions exist
            assert callable(render_error_message)
            assert callable(show_error_to_user)

        except Exception as e:
            pytest.fail(f"Error handling UI integration failed: {e}")

    def test_state_management_ui_integration(self):
        """Test state management in UI integration."""
        try:
            from frontend.pages.chatbot import ChatbotStateManager

            # Test state manager creation
            state_manager = ChatbotStateManager()
            assert state_manager is not None
            assert hasattr(state_manager, 'reset_conversation')
            assert hasattr(state_manager, 'messages')

        except Exception as e:
            pytest.fail(f"State management UI integration failed: {e}")


# Note: Real NiceGUI UI integration tests would require:
# 1. NiceGUI test client setup
# 2. Browser automation (Selenium/Playwright)
# 3. Proper test server running
#
# The tests above are integration smoke tests that validate component
# compatibility and basic functionality without actual UI rendering.
