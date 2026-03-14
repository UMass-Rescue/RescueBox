"""
Example: Using Stepper Component in Chatbot Workflow

This file demonstrates how to integrate the WorkflowStepper component
into the chatbot interface to show progress through the workflow.

Workflow Steps:
1. Message Sent - User sends message
2. Tool Selection - Assistant selects tool
3. Form Filled - User fills form
4. Job Submitted - Form submitted
5. Results Ready - Results displayed

Usage:
    See chatbot.py for integration example
"""

import logging
from nicegui import ui
from frontend.components.shared.stepper import WorkflowStepper

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Define workflow steps for chatbot
CHATBOT_WORKFLOW_STEPS = [
    'Message Sent',
    'Tool Selected',
    'Form Ready',
    'Submitting',
    'Results Ready'
]


def create_chatbot_stepper(container: ui.element) -> WorkflowStepper:
    """
    Create stepper for chatbot workflow.
    
    Args:
        container: Container to render stepper into
    
    Returns:
        WorkflowStepper instance
    """
    return WorkflowStepper(
        steps=CHATBOT_WORKFLOW_STEPS,
        current_step=0,
        container=container
    )

