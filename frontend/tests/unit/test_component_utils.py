"""
Unit tests for component utilities.
"""

from unittest.mock import patch

from frontend.components.component_utils import (
    create_card_container,
    format_timestamp,
    get_component_theme_colors,
    log_component_event,
    validate_component_config,
)


class TestComponentUtils:
    """Test component utility functions."""

    def test_format_timestamp_relative(self):
        """Test relative timestamp formatting."""
        from datetime import datetime, timedelta

        # Mock current time
        now = datetime.now()
        past_time = now - timedelta(hours=2)

        result = format_timestamp(past_time.isoformat())
        assert "hours ago" in result

    def test_format_timestamp_absolute(self):
        """Test absolute timestamp formatting."""
        timestamp = "2024-01-15T10:30:00"
        result = format_timestamp(timestamp, "absolute")
        assert "2024-01-15 10:30:00" == result

    def test_format_timestamp_short(self):
        """Test short timestamp formatting."""
        timestamp = "2024-01-15T10:30:00"
        result = format_timestamp(timestamp, "short")
        assert "01/15 10:30" == result

    def test_format_timestamp_invalid(self):
        """Test handling of invalid timestamp."""
        result = format_timestamp("invalid")
        assert result == "invalid"

    def test_create_card_container(self):
        """Test create card container function exists."""
        # Just test that the function exists and is callable
        # Full UI testing would require NiceGUI context
        assert callable(create_card_container)

    def test_validate_component_config_valid(self):
        """Test validating valid component config."""
        config = {"key1": "value1", "key2": 42}
        required = ["key1", "key2"]

        assert validate_component_config(config, required) is True

    def test_validate_component_config_missing_key(self):
        """Test validating config with missing required key."""
        config = {"key1": "value1"}
        required = ["key1", "key2"]

        assert validate_component_config(config, required) is False

    def test_validate_component_config_none_value(self):
        """Test validating config with None value for required key."""
        config = {"key1": None}
        required = ["key1"]

        assert validate_component_config(config, required) is False

    def test_get_component_theme_colors(self):
        """Test getting theme colors for components."""
        success_colors = get_component_theme_colors("success")
        assert success_colors["bg"] == "bg-green-50"
        assert success_colors["border"] == "border-green-300"
        assert success_colors["text"] == "text-green-700"

        error_colors = get_component_theme_colors("error")
        assert error_colors["bg"] == "bg-red-50"
        assert error_colors["border"] == "border-red-300"

        unknown_colors = get_component_theme_colors("unknown")
        assert unknown_colors == get_component_theme_colors("info")

    @patch("frontend.components.component_utils.logger")
    def test_log_component_event(self, mock_logger):
        """Test logging component events."""
        log_component_event("TestComponent", "test_event", {"detail": "info"})

        mock_logger.info.assert_called_once_with(
            "TestComponent: test_event - {'detail': 'info'}"
        )
