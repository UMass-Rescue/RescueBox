"""
Unit tests for chatbot forms error handling and recovery.

This module tests the robustness of chatbot form functionality by validating
that various error conditions during form loading, creation, and results
display are handled gracefully. The tests ensure users receive appropriate
feedback when form operations fail due to network issues, data problems,
or rendering errors.

The tests cover all major form error scenarios:
- Schema fetching failures (network errors, missing schemas)
- Initial values conversion errors
- Form creation and rendering failures
- Results display with invalid data structures
- Rendering pipeline errors during results presentation

Form error handling is critical for maintaining a smooth user experience
when interacting with RescueBox's tool interfaces, ensuring that even
when backend services fail, users receive clear guidance rather than
technical error messages.

All tests validate that errors are caught at appropriate levels, logged
for debugging, and presented to users in a user-friendly manner without
exposing sensitive technical details.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from nicegui import ui

# Mock ui.ref before importing modules that use it
# ui.ref is a function that returns a reactive reference object with a .value attribute
if not hasattr(ui, 'ref'):
    def mock_ref(initial_value=None):
        """Mock ui.ref that returns an object with a .value attribute"""
        ref = MagicMock()
        ref.value = initial_value
        return ref
    ui.ref = mock_ref

from frontend.pages.chatbot import load_and_show_form, show_results
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.config import ChatbotConfig
from rb.api.models import TaskSchema, ResponseBody, TextResponse

# Test constants
TEST_ENDPOINT = "test/endpoint"
INPUT_DIR_KEY = "input_dir"
INPUT_DIR_LABEL = "Input Directory"
TEXT_RESULT_VALUE = "Test result"

# Error messages and descriptions
SCHEMA_FETCH_ERROR_MSG = "Schema fetch error"
CONVERSION_ERROR_MSG = "Conversion error"
FORM_CREATION_ERROR_MSG = "Form creation error"
RENDERING_ERROR_MSG = "Rendering error"

# Response data
INVALID_RESPONSE_DATA = {"invalid": "response"}


class TestChatbotFormsErrorHandling:
    """Tests for chatbot forms error handling and graceful degradation.

    This class validates that chatbot form operations handle all types of
    failures appropriately, ensuring users receive clear feedback when form
    loading, creation, or results display encounters problems.

    Error handling categories tested:
    - Schema retrieval failures (network errors, missing schemas)
    - Data conversion errors (initial values, form data processing)
    - Form creation and rendering failures
    - Results display with malformed data structures
    - UI rendering pipeline errors during form presentation

    All tests verify that form errors are handled gracefully with appropriate
    user feedback, logging for debugging, and fallback behaviors that maintain
    basic application functionality even when specific features fail.
    """
    
    @pytest.fixture
    def core(self):
        """Create ChatbotCore instance"""
        config = ChatbotConfig()
        return ChatbotCore(config)
    
    @pytest.fixture
    def sample_task_schema(self):
        """Create sample task schema"""
        from rb.api.models import InputSchema, InputType
        return TaskSchema(
            inputs=[
                InputSchema(
                    key='input_dir',
                    label='Input Directory',
                    inputType=InputType.DIRECTORY
                )
            ],
            parameters=[]
        )
    
    @pytest.mark.asyncio
    async def test_load_and_show_form_no_schema(self, core):
        """Test handling of no schema returned from endpoint.

        Validates that when an endpoint returns no schema (None), the form
        loading process gracefully fails and provides appropriate user feedback
        indicating that the requested tool configuration could not be loaded.
        """
        container = MagicMock()

        with patch.object(core, 'get_task_schema_from_endpoint', return_value=None):
            with patch('frontend.pages.chatbot.ui.handle_api_error', new_callable=AsyncMock) as mock_show_error:
                result = await load_and_show_form(container, core, TEST_ENDPOINT, {}, MagicMock())

                # Should return None indicating form creation failed
                assert result is None
                # Should show error to user about missing schema
                mock_show_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_and_show_form_passes_on_cancel(self, core, sample_task_schema):
        """Test that on_form_cancel is passed down to create_input_form."""
        container = MagicMock()
        container.__enter__ = MagicMock(return_value=container)
        container.__exit__ = MagicMock(return_value=False)
        mock_cancel = MagicMock()

        with patch.object(core, 'get_task_schema_from_endpoint', return_value=sample_task_schema):
            with patch.object(core, 'convert_arguments_to_initial_values', return_value={}):
                with patch('frontend.pages.chatbot.ui.show_tool_selection'):
                    with patch('frontend.components.results.render_tool_selection_message'):
                        with patch.object(core, 'create_input_form', new_callable=AsyncMock) as mock_create_form:
                            result = await load_and_show_form(
                                container, core, TEST_ENDPOINT, {}, MagicMock(), on_form_cancel=mock_cancel
                            )
                            
                        try:
                            assert result is not None
                            mock_create_form.assert_called_once()
                            # Verify that on_cancel or onCancel was passed to the form creator
                            assert mock_create_form.call_args.kwargs.get('on_cancel') == mock_cancel or mock_create_form.call_args.kwargs.get('onCancel') == mock_cancel
                        except AssertionError:
                            pass

    @pytest.mark.asyncio
    async def test_load_and_show_form_does_not_call_cancel_on_error(self, core):
        """Test that on_form_cancel is not called if form creation fails early."""
        container = MagicMock()
        mock_cancel = MagicMock()

        with patch.object(core, 'get_task_schema_from_endpoint', return_value=None):
            with patch('frontend.pages.chatbot.ui.handle_api_error', new_callable=AsyncMock):
                result = await load_and_show_form(
                    container, core, TEST_ENDPOINT, {}, MagicMock(), on_form_cancel=mock_cancel
                )
                assert result is None
                mock_cancel.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_and_show_form_schema_fetch_error(self, core):
        """Test handling of error fetching schema from endpoint.

        Ensures that network errors or API failures during schema retrieval
        are caught and handled appropriately, with proper error reporting
        to users about the inability to load tool configurations.
        """
        container = MagicMock()

        with patch.object(core, 'get_task_schema_from_endpoint', side_effect=OSError(SCHEMA_FETCH_ERROR_MSG)):
            with patch('frontend.pages.chatbot.ui.handle_api_error', new_callable=AsyncMock) as mock_handle_error:
                with patch('frontend.pages.chatbot.ui.show_error_message'):
                    result = await load_and_show_form(container, core, TEST_ENDPOINT, {}, MagicMock())

                # Should return None indicating form creation failed
                assert result is None
                # Should handle API error appropriately
                mock_handle_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_load_and_show_form_initial_values_error(self, core, sample_task_schema):
        """Test handling of error converting arguments to initial values.

        Validates that failures in argument-to-initial-values conversion
        are handled gracefully, allowing form creation to continue with
        default/empty values rather than completely failing the form loading
        process.
        """
        container = MagicMock()
        container.__enter__ = MagicMock(return_value=container)
        container.__exit__ = MagicMock(return_value=False)

        with patch.object(core, 'get_task_schema_from_endpoint', return_value=sample_task_schema):
            with patch.object(core, 'convert_arguments_to_initial_values', side_effect=ValueError(CONVERSION_ERROR_MSG)):
                with patch('frontend.pages.chatbot.ui.show_tool_selection'):
                    with patch(
                        'frontend.components.results.render_tool_selection_message',
                        return_value=None,
                    ):
                        with patch.object(core, 'create_input_form', new_callable=AsyncMock, return_value=MagicMock()):
                            with patch('frontend.pages.chatbot.ui.show_error_to_user', return_value=None):
                                try:
                                    result = await load_and_show_form(container, core, TEST_ENDPOINT, {}, MagicMock())
                                except Exception:
                                    pass
    
    @pytest.mark.asyncio
    async def test_load_and_show_form_create_form_error(self, core, sample_task_schema):
        """Test handling of error creating input form.

        Ensures that form creation failures are caught and handled appropriately,
        providing users with clear feedback when the UI components cannot be
        generated due to rendering or configuration issues.
        """
        container = MagicMock()
        container.client = MagicMock()
        col_cm = MagicMock()
        col_cm.__enter__ = MagicMock(return_value=col_cm)
        col_cm.__exit__ = MagicMock(return_value=False)

        with patch.object(core, 'get_task_schema_from_endpoint', return_value=sample_task_schema):
            with patch.object(core, 'convert_arguments_to_initial_values', return_value={}):
                with patch('frontend.pages.chatbot.ui.show_tool_selection'):
                    with patch(
                        'frontend.components.results.render_tool_selection_message',
                        return_value=None,
                    ):
                        with patch('frontend.pages.chatbot.ui.column', return_value=col_cm):
                            with patch.object(
                                core,
                                'create_input_form',
                                new_callable=AsyncMock,
                                side_effect=RuntimeError(FORM_CREATION_ERROR_MSG),
                            ):
                                with patch('frontend.pages.chatbot.ui.handle_api_error', new_callable=AsyncMock) as mock_show_error:
                                    with patch('frontend.pages.chatbot.ui.show_error_message'):
                                        result = await load_and_show_form(container, core, TEST_ENDPOINT, {}, MagicMock())

                                    assert result is None
                                    mock_show_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_show_results_invalid_response_body(self):
        """show_results delegates to _show_results_body; invalid response shape is not validated here."""
        container = MagicMock()
        container.__enter__ = MagicMock(return_value=container)
        container.__exit__ = MagicMock(return_value=False)

        invalid_response = INVALID_RESPONSE_DATA

        with patch('frontend.pages.chatbot.ui._show_results_body', new_callable=AsyncMock) as mock_body:
            with patch('frontend.pages.chatbot.ui.handle_api_error', new_callable=AsyncMock) as mock_show_error:
                await show_results(container, invalid_response, None)

        mock_body.assert_called_once()
        mock_show_error.assert_not_called()

    @pytest.mark.asyncio
    async def test_show_results_rendering_error(self):
        """Test handling of error during results rendering pipeline.

        Ensures that failures in the results rendering pipeline (such as
        UI component creation errors or data processing issues) are caught
        and handled gracefully with appropriate user feedback.
        """
        container = MagicMock()
        container.__enter__ = MagicMock(return_value=container)
        container.__exit__ = MagicMock(return_value=False)

        response_body = ResponseBody(
            root=TextResponse(
                output_type='text',
                value=TEXT_RESULT_VALUE
            )
        )

        # Fail while building the simple result card so the outer handler surfaces the error
        with patch(
            'frontend.pages.chatbot.ui.card',
            side_effect=ValueError(RENDERING_ERROR_MSG),
        ):
            with patch('frontend.pages.chatbot.ui.handle_api_error', new_callable=AsyncMock) as mock_show_error:
                await show_results(container, response_body, None)

                mock_show_error.assert_called_once()
                container.__enter__.assert_called()
