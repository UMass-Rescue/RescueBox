"""Shared UI: navbar, breadcrumbs, notifications, layout helpers, stepper."""

from __future__ import annotations

import logging
import sys

from nicegui import ui

from frontend.components.shared.breadcrumbs import create_breadcrumbs
from frontend.components.shared.layout import (
    render_loading_row,
    render_page_header,
)
from frontend.components.shared.navbar import create_navbar
from frontend.components.shared.notifications import (
    notify_error,
    notify_info,
    notify_success,
    notify_warning,
)
from frontend.components.shared.stepper import (
    WorkflowStepper,
    create_workflow_stepper,
)

logger = logging.getLogger(__name__)

__all__ = [
    "WorkflowStepper",
    "create_breadcrumbs",
    "create_navbar",
    "create_workflow_stepper",
    "notify_error",
    "notify_info",
    "notify_success",
    "notify_warning",
    "render_loading_row",
    "render_page_header",
    "ui",
]

# Legacy submodule aliases for tests that patch e.g.
# ``frontend.components.shared.notifications`` (documented in frontend/readme.md).
notifications = sys.modules[__name__]
navbar = create_navbar
breadcrumbs = sys.modules[__name__]
stepper = sys.modules[__name__]
