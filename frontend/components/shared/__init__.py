"""Shared UI: navbar, breadcrumbs, notifications, layout helpers, stepper."""

from __future__ import annotations

import logging
import sys

from frontend.components.shared.breadcrumbs import (
    create_breadcrumbs,
    create_job_breadcrumbs,
)
from frontend.components.shared.layout import (
    render_error_card,
    render_loading_row,
    render_page_header,
    render_success_card,
)
from frontend.components.shared.navbar import create_navbar
from frontend.components.shared.notifications import (
    notify_error,
    notify_info,
    notify_success,
    notify_warning,
)
from frontend.components.shared.stepper import (
    CHATBOT_WORKFLOW_STEPS,
    WorkflowStepper,
    create_chatbot_stepper,
    create_workflow_stepper,
)
from nicegui import ui

logger = logging.getLogger(__name__)

__all__ = [
    "notify_success",
    "notify_error",
    "notify_info",
    "notify_warning",
    "create_breadcrumbs",
    "create_job_breadcrumbs",
    "create_navbar",
    "render_loading_row",
    "render_error_card",
    "render_success_card",
    "render_page_header",
    "WorkflowStepper",
    "create_workflow_stepper",
    "CHATBOT_WORKFLOW_STEPS",
    "create_chatbot_stepper",
    "ui",
]

# Legacy submodule aliases for tests that patch e.g.
# ``frontend.components.shared.notifications`` (documented in frontend/readme.md).
notifications = sys.modules[__name__]
navbar = create_navbar
breadcrumbs = sys.modules[__name__]
stepper = sys.modules[__name__]
