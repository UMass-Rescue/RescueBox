"""
Unit tests for shared UI components.

This module tests the shared components like navbar and breadcrumbs.
Notification behavior is covered in ``test_notifications.py``.
"""

from unittest.mock import patch, MagicMock

from frontend.components.shared import create_navbar
from frontend.components.shared import create_breadcrumbs


class TestNavbar:
    """Test navbar component functionality."""

    def test_create_navbar_structure(self):
        """Test navbar creation function exists."""
        # Just test that the function exists and is callable
        # Full UI testing would require NiceGUI context
        assert callable(create_navbar)


class TestBreadcrumbs:
    """Test breadcrumb component."""

    @patch("frontend.components.shared.ui")
    def test_create_breadcrumbs_structure(self, mock_ui):
        """Test breadcrumb creation."""
        mock_row = MagicMock()
        mock_ui.row.return_value.__enter__ = MagicMock(return_value=mock_row)
        mock_ui.row.return_value.__exit__ = MagicMock()

        breadcrumbs = [
            {"label": "Home", "path": "/"},
            {"label": "Jobs", "path": "/jobs"},
            {"label": "Job Details", "path": "/jobs/123"},
        ]

        result = create_breadcrumbs(breadcrumbs)

        # Verify basic structure
        mock_ui.row.assert_called_once()
        assert result is not None


class TestSharedComponentsIntegration:
    """Integration tests for shared components."""

    def test_shared_components_coordination(self):
        """Test that shared components work together."""
        from frontend.components.shared import (
            navbar,
            notifications,
            breadcrumbs,
            stepper,
        )

        # Verify all modules are available
        assert navbar is not None
        assert notifications is not None
        assert breadcrumbs is not None
        assert stepper is not None

    def test_shared_component_exports(self):
        """Test that shared components export expected functions."""
        from frontend.components.shared import create_navbar, create_breadcrumbs

        # Verify key functions are exported
        assert callable(create_navbar)
        assert callable(create_breadcrumbs)
