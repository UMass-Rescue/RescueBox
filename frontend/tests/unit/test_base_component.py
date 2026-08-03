"""
Unit tests for base component classes.

This module tests the base component infrastructure including BaseComponent,
ComponentRegistry, and component utilities.
"""

from unittest.mock import MagicMock, patch

from frontend.components.base_component import BaseComponent, ComponentRegistry
from frontend.components.component_utils import (
    create_card_container,
    format_timestamp,
    get_component_theme_colors,
    log_component_event,
    validate_component_config,
)


class TestBaseComponent:
    """Test BaseComponent class functionality."""

    def test_base_component_initialization(self):
        """Test BaseComponent initialization with config."""

        # Create a concrete subclass for testing
        class TestComponent(BaseComponent):
            def render(self):
                return None

        config = {"test_key": "test_value"}
        component = TestComponent(**config)

        assert component.config == config
        assert component.logger is not None
        assert component.logger.name == "TestComponent"

    def test_base_component_render_abstract(self):
        """Test that render method can be overridden."""

        # Create a concrete subclass for testing
        class TestComponent(BaseComponent):
            def render(self):
                return "rendered"

        component = TestComponent()
        assert component.render() == "rendered"

    @patch("frontend.components.base_component.ui")
    def test_create_error_display(self, mock_ui):
        """Test creating error display."""

        # Create a concrete subclass for testing
        class TestComponent(BaseComponent):
            def render(self):
                return None

        component = TestComponent()

        # Mock the context manager
        mock_card = MagicMock()
        mock_card_context = MagicMock()
        mock_card_context.__enter__ = MagicMock(return_value=mock_card)
        mock_card_context.__exit__ = MagicMock()
        mock_ui.card.return_value = mock_card_context

        component.create_error_display("Test error")

        mock_ui.card.assert_called_once()
        mock_ui.label.assert_any_call("Error")
        mock_ui.label.assert_any_call("Test error")

    @patch("frontend.components.base_component.ui")
    def test_create_loading_display(self, mock_ui):
        """Test creating loading display."""

        # Create a concrete subclass for testing
        class TestComponent(BaseComponent):
            def render(self):
                return None

        component = TestComponent()

        # Mock the context manager
        mock_row = MagicMock()
        mock_row_context = MagicMock()
        mock_row_context.__enter__ = MagicMock(return_value=mock_row)
        mock_row_context.__exit__ = MagicMock()
        mock_ui.row.return_value = mock_row_context

        component.create_loading_display("Custom loading...")

        mock_ui.row.assert_called_once()
        mock_ui.spinner.assert_called_once_with(size="sm")
        mock_ui.label.assert_called_once_with("Custom loading...")

    @patch("frontend.components.component_utils.ui")
    def test_create_success_display(self, mock_ui):
        """Test creating success display."""

        # Create a concrete subclass for testing
        class TestComponent(BaseComponent):
            def render(self):
                return None

        component = TestComponent()

        # Mock the context manager
        mock_card = MagicMock()
        mock_card_context = MagicMock()
        mock_card_context.__enter__ = MagicMock(return_value=mock_card)
        mock_card_context.__exit__ = MagicMock()
        mock_ui.card.return_value = mock_card_context

        component.create_success_display("Operation successful")

        mock_ui.card.assert_called_once()
        mock_ui.label.assert_any_call("Success")
        mock_ui.label.assert_any_call("Operation successful")

    @patch("logging.getLogger")
    def test_log_action(self, mock_get_logger):
        """Test logging component actions."""

        # Create a concrete subclass for testing
        class TestComponent(BaseComponent):
            def render(self):
                return None

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        component = TestComponent()
        component.log_action("test_action", {"detail": "value"})

        # Check that log_action was called (logger is called during init too)
        assert any(
            "test_action" in str(call) for call in mock_logger.info.call_args_list
        )
        assert any(
            "{'detail': 'value'}" in str(call)
            for call in mock_logger.info.call_args_list
        )


class TestComponentRegistry:
    """Test ComponentRegistry functionality."""

    def test_registry_initialization(self):
        """Test registry starts empty."""
        assert ComponentRegistry._instances == {}
        assert ComponentRegistry.list_components() == []

    def test_register_component(self):
        """Test registering a component."""
        mock_component = MagicMock()
        ComponentRegistry.register("test_component", mock_component)

        assert ComponentRegistry.get("test_component") == mock_component
        assert "test_component" in ComponentRegistry.list_components()

    def test_get_nonexistent_component(self):
        """Test getting a component that doesn't exist."""
        assert ComponentRegistry.get("nonexistent") is None

    def test_unregister_component(self):
        """Test unregistering a component."""
        mock_component = MagicMock()
        ComponentRegistry.register("temp_component", mock_component)
        assert ComponentRegistry.get("temp_component") is not None

        ComponentRegistry.unregister("temp_component")
        assert ComponentRegistry.get("temp_component") is None
        assert "temp_component" not in ComponentRegistry.list_components()


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
