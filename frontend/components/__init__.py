"""Components package"""

from frontend.components.shared import (
    create_navbar,
    navbar,
    WorkflowStepper,
    create_workflow_stepper,
    notify_success,
    notify_error,
    notify_info,
    notify_warning,
)
from frontend.components.models import render_model_card
from frontend.components.jobs import render_job_row

# FormGenerator imported on-demand to avoid rb.api dependency in tests
from frontend.components.results import ResultsPreview
from frontend.components.base_component import BaseComponent, ComponentRegistry
from frontend.components.component_utils import (
    setup_component_imports,
    format_timestamp,
    create_card_container,
    validate_component_config,
    get_component_theme_colors,
    log_component_event,
)

__all__ = [
    "create_navbar",
    "navbar",
    "WorkflowStepper",
    "create_workflow_stepper",
    "notify_success",
    "notify_error",
    "notify_info",
    "notify_warning",
    "render_model_card",
    "render_job_row",
    "ResultsPreview",
    "BaseComponent",
    "ComponentRegistry",
    "setup_component_imports",
    "format_timestamp",
    "create_card_container",
    "validate_component_config",
    "get_component_theme_colors",
    "log_component_event",
]
