"""
Unit tests for notification system functionality.

This module tests the enhanced notification system that provides
consistent, user-friendly feedback for various application states
and operations. The tests validate proper display behavior, timing,
positioning, and logging for different notification types.

The notification system supports:
- Success notifications (green, positive feedback)
- Error notifications (red, problem indication)
- Info notifications (blue, neutral information)
- Warning notifications (orange/yellow, caution alerts)

All notifications include proper accessibility features, positioning,
and configurable duration settings.
"""

import pytest
from unittest.mock import patch

# Test constants
TEST_SUCCESS_MESSAGE = "Job completed successfully"
TEST_ERROR_MESSAGE = "Failed to submit job"
TEST_INFO_MESSAGE = "Processing your request..."
TEST_WARNING_MESSAGE = "Please check your input"
TEST_CUSTOM_MESSAGE = "Custom message"
TEST_CRITICAL_ERROR = "Critical error"

# Duration constants (in milliseconds)
DEFAULT_SUCCESS_TIMEOUT = 3000  # 3 seconds
DEFAULT_ERROR_TIMEOUT = 5000  # 5 seconds
DEFAULT_INFO_TIMEOUT = 3000  # 3 seconds
DEFAULT_WARNING_TIMEOUT = 4000  # 4 seconds
CUSTOM_TIMEOUT = 5000  # 5 seconds
PERSISTENT_TIMEOUT = 0  # No auto-hide

# Position constants
DEFAULT_POSITION = "top"
BOTTOM_POSITION = "bottom"


class TestNotifications:
    """Tests for notification system functions.

    This class validates the complete notification system including:
    - Different notification types (success, error, info, warning)
    - Customizable display parameters (position, duration, close button)
    - Proper logging integration
    - Parameter validation and edge cases
    """

    def test_notify_success(self):
        """Test success notification with default parameters.

        Validates that success notifications are displayed with correct
        styling (positive/green), default positioning (top), standard
        duration (3 seconds), and include a close button for user control.
        """
        from frontend.components.shared import notify_success

        with patch("nicegui.ui.notify") as mock_notify:
            notify_success(TEST_SUCCESS_MESSAGE)

            mock_notify.assert_called_once()
            call_args = mock_notify.call_args
            assert call_args[0][0] == TEST_SUCCESS_MESSAGE
            assert call_args[1]["type"] == "positive"
            assert call_args[1]["position"] == DEFAULT_POSITION
            assert call_args[1]["timeout"] == DEFAULT_SUCCESS_TIMEOUT
            assert call_args[1]["close_button"] is True

    def test_notify_success_custom_params(self):
        """Test success notification with custom parameters.

        Ensures that success notifications can be customized with
        different durations, positions, and close button settings
        while maintaining the correct notification type (positive).
        """
        from frontend.components.shared import notify_success

        with patch("nicegui.ui.notify") as mock_notify:
            notify_success(
                TEST_CUSTOM_MESSAGE,
                duration=5.0,
                position=BOTTOM_POSITION,
                close_button=False,
            )

            mock_notify.assert_called_once()
            call_args = mock_notify.call_args
            assert call_args[0][0] == TEST_CUSTOM_MESSAGE
            assert call_args[1]["type"] == "positive"
            assert call_args[1]["position"] == BOTTOM_POSITION
            assert call_args[1]["timeout"] == CUSTOM_TIMEOUT
            assert call_args[1]["close_button"] is False

    def test_notify_error(self):
        """Test error notification with default parameters.

        Validates that error notifications use appropriate styling
        (negative/red), longer default duration (5 seconds) for
        important error messages, and include close button.
        """
        from frontend.components.shared import notify_error

        with patch("nicegui.ui.notify") as mock_notify:
            notify_error(TEST_ERROR_MESSAGE)

            mock_notify.assert_called_once()
            call_args = mock_notify.call_args
            assert call_args[0][0] == TEST_ERROR_MESSAGE
            assert call_args[1]["type"] == "negative"
            assert call_args[1]["position"] == DEFAULT_POSITION
            assert call_args[1]["timeout"] == DEFAULT_ERROR_TIMEOUT
            assert call_args[1]["close_button"] is True

    def test_notify_error_persistent(self):
        """Test error notification with persistent duration.

        Ensures that critical errors can be made persistent (no auto-hide)
        by setting duration to 0, requiring user interaction to dismiss.
        """
        from frontend.components.shared import notify_error

        with patch("nicegui.ui.notify") as mock_notify:
            notify_error(TEST_CRITICAL_ERROR, duration=0)

            mock_notify.assert_called_once()
            call_args = mock_notify.call_args
            assert call_args[1]["timeout"] == PERSISTENT_TIMEOUT  # No auto-hide

    def test_notify_info(self):
        """Test info notification with default parameters.

        Validates that informational notifications use the medium-gray skin
        without Quasar ``type`` (so teal ``info`` does not override) and standard duration.
        """
        from frontend.components.shared import notify_info

        with patch("nicegui.ui.notify") as mock_notify:
            notify_info(TEST_INFO_MESSAGE)

            mock_notify.assert_called_once()
            call_args = mock_notify.call_args
            assert call_args.kwargs["message"] == TEST_INFO_MESSAGE
            assert "type" not in call_args.kwargs
            assert call_args.kwargs["position"] == DEFAULT_POSITION
            assert call_args.kwargs["timeout"] == DEFAULT_INFO_TIMEOUT
            assert "color" not in call_args.kwargs

    def test_notify_warning(self):
        """Test warning notification with default parameters.

        Ensures that warning notifications use appropriate caution styling
        (warning/orange) and slightly longer duration (4 seconds) to ensure
        users notice important caution messages.
        """
        from frontend.components.shared import notify_warning

        with patch("nicegui.ui.notify") as mock_notify:
            notify_warning(TEST_WARNING_MESSAGE)

            mock_notify.assert_called_once()
            call_args = mock_notify.call_args
            assert call_args[0][0] == TEST_WARNING_MESSAGE
            assert call_args[1]["type"] == "warning"
            assert call_args[1]["position"] == DEFAULT_POSITION
            assert call_args[1]["timeout"] == DEFAULT_WARNING_TIMEOUT

    def test_notify_logging(self):
        """Test that notifications include proper logging.

        Validates that notifications are logged at debug level for
        troubleshooting and audit purposes, ensuring system administrators
        can track user interactions and system feedback.
        """
        from frontend.components.shared import notify_success

        with patch("nicegui.ui.notify"):
            with patch(
                "frontend.components.shared.notifications.logger"
            ) as mock_logger:
                notify_success("Test message")

                # Should log debug message for audit trail
                mock_logger.debug.assert_called_once()
                assert "Success notification shown" in mock_logger.debug.call_args[0][0]

    @pytest.mark.parametrize("position", ["top", "bottom", "left", "right"])
    def test_notify_positions(self, position):
        """Test notifications with different display positions.

        Ensures that notifications can be positioned in all supported
        locations (top, bottom, left, right) to accommodate different
        UI layouts and user preferences.
        """
        from frontend.components.shared import notify_success

        with patch("nicegui.ui.notify") as mock_notify:
            notify_success("Test", position=position)

            call_args = mock_notify.call_args
            assert call_args[1]["position"] == position
