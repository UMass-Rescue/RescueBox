"""
Form Submit Handler

This module provides the FormSubmitHandler class for handling form submission
and job execution in the chatbot interface.
"""

import logging
from typing import Optional, List, Dict, Any
from nicegui import ui
from rb.api.models import TaskSchema
from frontend.pages.chatbot.utils.ui_operations import UIOperations
from frontend.chatbot.core import ChatbotCore
from frontend.pages.chatbot.utils.job_submission_orchestrator import JobSubmissionOrchestrator
from frontend.components.forms.case_notes_dialog import show_case_notes_dialog


# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FormSubmitHandler:
    """
    Handles form submission and job execution for the chatbot.

    This class manages the complete flow from form submission through job
    execution and result display.
    """

    def __init__(self, state_manager):
        """
        Initialize the form submit handler.

        Args:
            state_manager: ChatbotStateManager instance
        """
        self.state_manager = state_manager
        self.job_orchestrator = JobSubmissionOrchestrator(self)

        logger.debug("FormSubmitHandler initialized")

    async def submit_form(self,
                         request_body,
                         endpoint: str,
                         task_schema: TaskSchema,
                         container,
                         core: ChatbotCore,
                         remaining_calls: Optional[List[Dict[str, Any]]] = None,
                         conversation_id: Optional[str] = None):
        """
        Submit a form and handle the complete job execution flow.

        Args:
            request_body: Validated request body
            endpoint: API endpoint name
            task_schema: Task schema for the endpoint
            container: UI container for displaying results
            core: ChatbotCore instance
            remaining_calls: Remaining tool calls in sequence
            conversation_id: Conversation ID for message saving
        """
        from frontend.utils.nicegui_storage import ensure_user_id
        if ensure_user_id() is None:
            return False

        # Show case notes modal before submitting
        case_notes = await show_case_notes_dialog()
        if case_notes is None:
            logger.debug("User cancelled case notes dialog, aborting submission")
            return False

        # Scroll to bottom to ensure the user sees the progress
        UIOperations.scroll_to_bottom()

        await self.job_orchestrator.submit_job(
            request_body, endpoint, task_schema, container, core,
            remaining_calls, conversation_id, case_notes=case_notes or None
        )
        return True

    def _report_error(self, title: str, details: str = None):
        """Report an error (placeholder for future implementation)."""
        logger.info("Error reported by user: %s - %s", title, details or "No details")
        # TODO: Implement error reporting functionality
        ui.notify("Error report submitted. Thank you for helping improve RescueBox!", type="positive", classes="rb-notify-505759")

    def get_submission_status(self) -> dict:
        """
        Get the current submission status.

        Returns:
            dict: Status information
        """
        return {
            'is_processing': self.state_manager.is_processing,
            'status_text': self.state_manager.status_text,
            'conversation_id': self.state_manager.conversation_id
        }
