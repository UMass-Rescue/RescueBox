"""
Job Components Package

This package contains modular components for rendering job-related UI elements.
"""

from frontend.pages.jobs.components.job_metadata import extract_job_fields, render_model_info, render_job_metadata
from frontend.pages.jobs.components.job_actions import render_job_action_buttons
from frontend.pages.jobs.components.job_forms import render_compact_inputs_summary, render_readonly_form
from frontend.pages.jobs.components.job_status import render_error_status

__all__ = [
    'extract_job_fields',
    'render_model_info',
    'render_job_metadata',
    'render_job_action_buttons',
    'render_compact_inputs_summary',
    'render_readonly_form',
    'render_error_status',
]
