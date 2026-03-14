"""
Unit tests for shared UI components.

This module tests the shared components like navbar, notifications, breadcrumbs, etc.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from nicegui import ui

from frontend.components.shared.navbar import create_navbar
from frontend.components.shared.notifications import notify_success, notify_error, notify_info, notify_warning
from frontend.components.shared.breadcrumbs import create_breadcrumbs


class TestNavbar:
    """Test navbar component functionality."""

    def test_create_navbar_structure(self):
        """Test navbar creation function exists."""
        # Just test that the function exists and is callable
        # Full UI testing would require NiceGUI context
        assert callable(create_navbar)

    def test_navbar_import(self):
        """Test navbar module imports correctly."""
        from frontend.components.shared import navbar
        assert navbar is not None
        assert hasattr(navbar, 'create_navbar')


class TestNotifications:
    """Test notification system."""

    def test_notify_success(self):
        """Test success notification function exists."""
        assert callable(notify_success)

    def test_notify_error(self):
        """Test error notification function exists."""
        assert callable(notify_error)

    def test_notify_warning(self):
        """Test warning notification function exists."""
        assert callable(notify_warning)

    def test_notify_info(self):
        """Test info notification function exists."""
        assert callable(notify_info)

    def test_notifications_import(self):
        """Test notifications module imports correctly."""
        from frontend.components.shared import notifications
        assert notifications is not None
        assert hasattr(notifications, 'notify_success')
        assert hasattr(notifications, 'notify_error')
        assert hasattr(notifications, 'notify_info')
        assert hasattr(notifications, 'notify_warning')


class TestBreadcrumbs:
    """Test breadcrumb component."""

    @patch('frontend.components.shared.breadcrumbs.ui')
    def test_create_breadcrumbs_structure(self, mock_ui):
        """Test breadcrumb creation."""
        mock_row = MagicMock()
        mock_ui.row.return_value.__enter__ = MagicMock(return_value=mock_row)
        mock_ui.row.return_value.__exit__ = MagicMock()

        breadcrumbs = [
            {"label": "Home", "path": "/"},
            {"label": "Jobs", "path": "/jobs"},
            {"label": "Job Details", "path": "/jobs/123"}
        ]

        result = create_breadcrumbs(breadcrumbs)

        # Verify basic structure
        mock_ui.row.assert_called_once()
        assert result is not None

    def test_breadcrumbs_import(self):
        """Test breadcrumbs module imports correctly."""
        from frontend.components.shared import breadcrumbs
        assert breadcrumbs is not None
        assert hasattr(breadcrumbs, 'create_breadcrumbs')


class TestStepper:
    """Test stepper component."""

    def test_stepper_import(self):
        """Test stepper module imports correctly."""
        from frontend.components.shared import stepper
        assert stepper is not None

    def test_stepper_example_import(self):
        """Test stepper example imports correctly."""
        from frontend.components.shared import stepper_example
        assert stepper_example is not None


class TestSharedComponentsIntegration:
    """Integration tests for shared components."""

    def test_shared_components_coordination(self):
        """Test that shared components work together."""
        from frontend.components.shared import (
            navbar, notifications, breadcrumbs, stepper
        )

        # Verify all modules are available
        assert navbar is not None
        assert notifications is not None
        assert breadcrumbs is not None
        assert stepper is not None

    def test_shared_component_exports(self):
        """Test that shared components export expected functions."""
        from frontend.components.shared import (
            create_navbar,
            create_breadcrumbs
        )
        from frontend.components.shared.notifications import (
            notify_success, notify_error
        )

        # Verify key functions are exported
        assert callable(create_navbar)
        assert callable(notify_success)
        assert callable(notify_error)
        assert callable(create_breadcrumbs)
