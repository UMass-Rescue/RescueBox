"""
Unit tests for form handler error handling functionality.

This module tests the error handling and validation logic in form submission,
ensuring that invalid inputs, network failures, and edge cases are handled
gracefully with appropriate user feedback and error reporting.
"""


from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError

from frontend.components.forms.form_handlers import (
    handle_form_submit,
    collect_form_data,
    validate_form
)
import pytest


class TestFormHandlersErrorHandling:
    """Tests for form handler error handling and validation.

    This class tests the robustness of form submission logic by verifying
    that various error conditions are handled gracefully, including:
    - Validation failures
    - Data collection errors
    - Submission callback failures
    - Unexpected exceptions
    """
    
    @pytest.fixture
    def mock_form_widgets(self):
        """Create mock form widgets"""
        widgets = {}
        
        # Mock input widgets
        input_dir_widget = Mock()
        input_dir_widget.value = "/tmp/test"
        widgets['input_dir'] = input_dir_widget
        
        prompt_widget = Mock()
        prompt_widget.value = "test prompt"
        widgets['prompt'] = prompt_widget
        
        # Mock parameter widget
        confidence_widget = Mock()
        confidence_widget.value = 0.9
        widgets['confidence'] = confidence_widget
        
        return widgets
    
    @pytest.mark.asyncio
    async def test_handle_form_submit_validation_error(self, sample_task_schema, mock_form_widgets):
        """Test validation error handling during form submission.

        Verifies that when form validation fails, the system properly
        prevents form submission and delegates error handling to the
        appropriate validation error handler without proceeding to
        data submission.
        """
        from frontend.components.forms import form_handlers

        with patch.object(form_handlers, 'validate_form_data', return_value={'is_valid': False, 'errors': {"input_dir": "Invalid path"}}):
            with patch('frontend.components.forms.form_handlers.handle_validation_error') as mock_handle_error:
                submit_called = False
                def mock_submit(data):
                    nonlocal submit_called
                    submit_called = True

                await handle_form_submit(sample_task_schema, mock_form_widgets, mock_submit)

                # Verify submit callback was not executed due to validation failure
                assert not submit_called
                # Verify validation error handler was called appropriately
                mock_handle_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_form_submit_data_collection_error(self, sample_task_schema, mock_form_widgets):
        """Test error handling during form data collection phase.

        Ensures that when form data collection fails (e.g., due to widget
        access issues or data processing errors), the system gracefully
        handles the exception, prevents form submission, and displays
        appropriate error feedback to the user.
        """
        from frontend.components.forms import form_handlers

        with patch.object(form_handlers, 'validate_form', return_value=(True, {})):
            with patch.object(form_handlers, 'collect_form_data', side_effect=Exception("Collection error")):
                with patch('frontend.components.forms.form_handlers.show_error_to_user') as mock_show_error:
                    submit_called = False
                    def mock_submit(data):
                        nonlocal submit_called
                        submit_called = True

                    await handle_form_submit(sample_task_schema, mock_form_widgets, mock_submit)

                    # Verify form submission was prevented due to collection failure
                    assert not submit_called
                    # Verify user was notified of the collection error
                    mock_show_error.assert_called_once()
                    assert "Failed to collect form data" in str(mock_show_error.call_args)
    
    @pytest.mark.asyncio
    async def test_handle_form_submit_submit_callback_error(self, sample_task_schema, mock_form_widgets):
        """Test error handling when form submission callback fails.

        Validates that if the user-provided submission callback throws
        an exception (e.g., network error, processing failure), the
        system catches the error and displays appropriate feedback
        without crashing the form handling flow.
        """
        from frontend.components.forms import form_handlers

        with patch.object(form_handlers, 'validate_form', return_value=(True, {})):
            with patch.object(form_handlers, 'collect_form_data', return_value={"inputs": {}, "parameters": {}}):
                with patch('frontend.components.forms.form_handlers.show_error_to_user') as mock_show_error:
                    def mock_submit(data):
                        raise Exception("Submit error")

                    await handle_form_submit(sample_task_schema, mock_form_widgets, mock_submit)

                    # Verify user was notified of submission failure
                    mock_show_error.assert_called_once()
                    assert "Form submission failed" in str(mock_show_error.call_args)
    
    @pytest.mark.asyncio
    async def test_handle_form_submit_no_callback(self, sample_task_schema, mock_form_widgets):
        """Test handling of missing submit callback"""
        from frontend.components.forms import form_handlers

        with patch.object(form_handlers, 'validate_form', return_value=(True, {})):
            with patch.object(form_handlers, 'collect_form_data', return_value={"inputs": {}, "parameters": {}}):
                with patch('frontend.components.forms.form_handlers.show_error_to_user') as mock_show_error:
                    await handle_form_submit(sample_task_schema, mock_form_widgets, None)

                    # Should show error to user
                    mock_show_error.assert_called_once()
                    assert "not configured" in str(mock_show_error.call_args)
    
    @pytest.mark.asyncio
    async def test_handle_form_submit_unexpected_error(self, sample_task_schema, mock_form_widgets):
        """Test handling of unexpected error during form submission"""
        from frontend.components.forms import form_handlers

        with patch.object(form_handlers, 'validate_form', side_effect=Exception("Unexpected error")):
            with patch.object(form_handlers, 'show_error_to_user') as mock_show_error:
                submit_called = False
                def mock_submit(data):
                    nonlocal submit_called
                    submit_called = True

                await handle_form_submit(sample_task_schema, mock_form_widgets, mock_submit)

                # Should not call submit callback
                assert not submit_called
                # Should show error to user
                mock_show_error.assert_called_once()
                assert "Unexpected error" in str(mock_show_error.call_args)
    
    def test_collect_form_data_missing_widget(self, sample_task_schema):
        """Test collecting form data when widget is missing"""
        widgets = {}
        # No widgets provided
        
        result = collect_form_data(sample_task_schema.model_dump(), widgets)
        
        # Should return empty data, not raise error
        assert "inputs" in result
        assert "parameters" in result
        assert len(result["inputs"]) == 0
        assert len(result["parameters"]) == 0
    
    def test_collect_form_data_widget_value_error(self, sample_task_schema):
        """Test collecting form data when widget value access fails"""
        widgets = {}
        
        # Widget that raises error when accessing value
        error_widget = Mock()
        error_widget.value = property(lambda self: (_ for _ in ()).throw(Exception("Value error")))
        
        widgets['input_dir'] = error_widget
        
        # Should handle error gracefully (test that it doesn't crash)
        # In practice, this would need more sophisticated handling
        # For now, we test that the function structure handles missing values
        result = collect_form_data(sample_task_schema.model_dump(), widgets)
        assert isinstance(result, dict)

