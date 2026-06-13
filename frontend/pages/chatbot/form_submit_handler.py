from __future__ import annotations

import logging
from typing import Any, List, Optional

from frontend.chatbot.core import ChatbotCore
from frontend.components.chat import UIOperations
from frontend.pages.chatbot.database_service import DatabaseService
from frontend.pages.chatbot.handlers import (
    JobSubmissionOrchestrator,
    show_case_notes_dialog,
)
from frontend.pages.chatbot.state import ChatbotStateManager
from frontend.pages.chatbot.handlers.job_submit_params import JobSubmitParams
from frontend.utils import ensure_active_case_id

logger = logging.getLogger(__name__)


class FormSubmitHandler:
    """Handles form submission and job execution for the chatbot."""

    def __init__(self, state_manager: ChatbotStateManager):
        self.state_manager = state_manager
        self.job_orchestrator = JobSubmissionOrchestrator(self)
        logger.debug("FormSubmitHandler initialized")

    async def submit_form(
        self,
        request_body,
        endpoint: str,
        task_schema,
        container,
        core: ChatbotCore,
        remaining_calls: Optional[List[dict[str, Any]]] = None,
        conversation_id: Optional[str] = None,
        **kwargs,
    ):
        """Submit a form and handle the complete job execution flow."""
        if ensure_active_case_id() is None:
            return False

        case_notes = await show_case_notes_dialog()
        if case_notes is None:
            logger.debug("User cancelled case notes dialog, aborting submission")
            return False

        if conversation_id:
            self.state_manager.set_conversation_id(conversation_id)
        await DatabaseService.ensure_active_conversation(self.state_manager)

        UIOperations.scroll_to_bottom()
        params = JobSubmitParams(
            request_body=request_body,
            endpoint=endpoint,
            task_schema=task_schema,
            container=container,
            core=core,
            remaining_calls=remaining_calls,
            conversation_id=self.state_manager.conversation_id,
        )
        await self.job_orchestrator.submit_job(
            params,
            case_notes=case_notes or None,
            **kwargs,
        )
        return True

    def active_conversation_id(self) -> Optional[str]:
        """Active conversation id from state (for tests and callers)."""
        return self.state_manager.conversation_id
