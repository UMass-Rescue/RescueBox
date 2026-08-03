import logging
import re
from typing import Optional, Dict, Any
from frontend.utils import set_logging_context
from frontend.database.chat_history_db import get_chat_history_db
from frontend.database.job_db import get_job_db
from frontend.database.job_models import JobStatus
from frontend.chatbot.config import ToolRegistry
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)


class DatabaseService:
    @staticmethod
    def get_job_db():
        return get_job_db()

    @staticmethod
    async def ensure_active_conversation(state_manager) -> str:
        """
        Guarantee a persisted conversation exists and is bound to ``state_manager``.

        Chat persistence and job history writes require ``conversation_id``
        without it,
        Menu-only flows (pick tool → Submit) never create a conversation row so History
        stays empty despite successful jobs.
        """
        cid = getattr(state_manager, "conversation_id", None)
        if cid:
            return cid
        chat_history = get_chat_history_db()
        conv = await chat_history.create_conversation()
        state_manager.set_conversation_id(conv.conversation_id)
        return conv.conversation_id

    @staticmethod
    def _should_apply_job_list_title(current_title: Optional[str]) -> bool:
        """
        Replace list title for default placeholders and for titles we set from a previous job
        (so a second job in the same thread updates the history row).
        Do not overwrite a user-visible title from the first chat message.
        """
        t = (current_title or "").strip()
        if not t:
            return True
        if re.match(r"^Conversation \d{4}-\d{2}-\d{2}$", t):
            return True
        # Titles we set: "Transcribe Audio · JOB_abc123"
        if re.match(r"^.{1,120} · JOB_[A-Za-z0-9_]+$", t):
            return True
        return False

    @staticmethod
    async def _set_conversation_list_title_from_job(
        conversation_id: str, endpoint: str, job_id: str
    ) -> None:
        chat_history = get_chat_history_db()
        conv = await chat_history.get_conversation(conversation_id)
        if not conv:
            return
        if not DatabaseService._should_apply_job_list_title(conv.title):
            return
        try:
            display = ToolRegistry.display_name_for_endpoint(endpoint)
        except UI_RENDER_ERRORS:
            display = (endpoint or "Job").split("/")[-1]
        new_title = f"{display} · {job_id}"
        if len(new_title) > 200:
            new_title = new_title[:197] + "..."
        await chat_history.update_conversation(conversation_id, title=new_title)

    @staticmethod
    async def save_message_to_history(
        conversation_id: str, role: str, content: str, **kwargs
    ):
        chat_history = get_chat_history_db()
        await chat_history.add_message(
            conversation_id=conversation_id, role=role, content=content, **kwargs
        )

    @staticmethod
    async def create_and_track_job(
        request_body, endpoint: str, task_schema=None, **kwargs
    ):

        job_db = get_job_db()
        job_record = await job_db.create_job(
            request_body=request_body,
            endpoint=endpoint,
            task_schema=task_schema,
            **kwargs,
        )
        if not job_record:
            return None
        job_id = getattr(job_record, "uid", None)
        if job_id:
            set_logging_context(job_id=job_id)
        return {"job_id": job_id, "status": "RUNNING"} if job_id else None

    @staticmethod
    async def update_job_status(job_uid: str, status: str, **kwargs):
        job_db = get_job_db()
        await job_db.update_job_status(uid=job_uid, status=status, **kwargs)

    @staticmethod
    def _job_request_snapshot(request_body: Any) -> Optional[Dict[str, Any]]:
        """Coerce submitted job payload to JSON-friendly ``inputs`` / ``parameters`` for history UI."""
        if request_body is None:
            return None
        try:
            if hasattr(request_body, "model_dump"):
                data = request_body.model_dump(mode="json")
            elif isinstance(request_body, dict):
                data = request_body
            else:
                return None
            snap: Dict[str, Any] = {}
            if "inputs" in data:
                snap["inputs"] = data["inputs"]
            if "parameters" in data:
                snap["parameters"] = data["parameters"]
            return snap or None
        except UI_RENDER_ERRORS:
            logger.debug(
                "Could not snapshot request body for chat history", exc_info=True
            )
            return None

    @staticmethod
    async def save_tool_call_to_history(
        conversation_id: str, endpoint: str, arguments: dict
    ):
        chat_history = get_chat_history_db()
        await chat_history.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=f"Selected tool: {endpoint}",
            message_type="tool_call",
            tool_calls=[{"name": endpoint, "arguments": arguments}],
        )

    @staticmethod
    async def save_job_started_to_history(
        conversation_id: str,
        endpoint: str,
        job_id: str,
        request_body: Any = None,
    ):
        chat_history = get_chat_history_db()
        snapshot = DatabaseService._job_request_snapshot(request_body)
        await chat_history.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=f"Job {job_id} started for {ToolRegistry.display_name_for_endpoint(endpoint)}",
            message_type="tool_result",
            tool_call_endpoint=endpoint,
            tool_call_arguments=snapshot,
            metadata={"job_id": job_id, "status": "RUNNING", "endpoint": endpoint},
        )
        try:
            await DatabaseService._set_conversation_list_title_from_job(
                conversation_id, endpoint, job_id
            )
        except UI_RENDER_ERRORS:
            logger.debug(
                "Could not update conversation list title from job", exc_info=True
            )

    @staticmethod
    async def save_tool_result_to_history(
        conversation_id: str, endpoint: str, job_id: Optional[str] = None
    ):
        chat_history = get_chat_history_db()
        content = (
            f"Job {job_id} completed successfully"
            if job_id
            else "Job completed successfully"
        )
        await chat_history.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            message_type="tool_result",
            tool_call_endpoint=endpoint,
            metadata=(
                {"job_id": job_id, "status": "completed"}
                if job_id
                else {"status": "completed"}
            ),
        )

    @staticmethod
    async def save_error_to_history(
        conversation_id: str, endpoint: str, error_message: str
    ):
        chat_history = get_chat_history_db()
        await chat_history.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=error_message,
            message_type="error",
            tool_call_endpoint=endpoint,
            metadata={"status": "failed"},
        )

    @staticmethod
    async def complete_job(job_id: str, response_body) -> bool:
        job_db = get_job_db()
        await job_db.update_job_status(
            uid=job_id,
            status=JobStatus.COMPLETED,
            response_body=response_body,
            status_text="",
        )
        return True

    @staticmethod
    async def save_user_prompt_if_missing_from_form_submission(
        conversation_id: str, prompt: str
    ):
        # Implementation if needed by tests
        pass

    @staticmethod
    def set_logging_context(**kwargs):
        return set_logging_context(**kwargs)


DatabaseService.DatabaseService = DatabaseService
