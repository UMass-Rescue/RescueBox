# frontend/chatbot/core.py
"""
Core Business Logic for Chatbot Operations

Coordinates API interactions, dynamic forms, job submission, and Granite (Ollama) tool selection.
"""
import json
import logging
from typing import Any

import httpx
from nicegui import ui
from rb.api.models import RequestBody, ResponseBody, TaskSchema

from frontend.api_client import ApiClient
from frontend.chatbot.api_helpers import fetch_task_schema
from frontend.chatbot.exceptions import CHATBOT_ERRORS
from frontend.chatbot.forms import create_input_form as _create
from frontend.chatbot.granite import parse_fine_tune_tool_response
from frontend.chatbot.orchestrator import submit_job_orchestrator
from frontend.chatbot.schema_utils import (
    convert_arguments_to_initial_values as _convert,
)
from frontend.chatbot.tool_config import create_advanced_granite_prompt

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ChatbotCore:
    """
    RescueBox API + Ollama coordinator.

    HTTP: ``self.api`` (ApiClient) is the primary entry; ``self.api_client`` is the
    underlying ``httpx.AsyncClient`` used by ``api_helpers`` fallbacks.
    """

    def __init__(self, config):
        self.config = config
        self.api = ApiClient(config.RESCUEBOX_HOST, timeout=config.TIMEOUT)
        self.api_client = self.api._client  # pylint: disable=protected-access
        self.ollama_url = config.OLLAMA_HOST
        logger.info("Granite tool OLLAMA_HOST: url=%s", self.ollama_url)

        self.ollama_client = httpx.AsyncClient(base_url=self.ollama_url, timeout=600.0)

    async def get_task_schema_from_endpoint(self, endpoint: str) -> TaskSchema | None:
        """Fetch and parse the TaskSchema for a plugin endpoint."""
        schema_dict = await fetch_task_schema(
            self.api,
            self.api_client,
            self.config,
            endpoint,
        )
        return TaskSchema(**schema_dict)

    def convert_arguments_to_initial_values(
        self, arguments: dict[str, Any], task_schema: TaskSchema, endpoint: str = ""
    ) -> dict[str, Any]:
        """Map tool arguments to form initial values."""
        return _convert(arguments, task_schema, endpoint)

    async def create_input_form(
        self,
        task_schema: TaskSchema,
        endpoint: str,
        initial_values: dict | None = None,
        on_submit: callable = None,
        on_cancel: callable = None,
        container: ui.element | None = None,
    ):
        """Render a NiceGUI form for the given task schema."""
        return await _create(
            task_schema,
            endpoint,
            initial_values=initial_values,
            on_submit=on_submit,
            on_cancel=on_cancel,
            container=container,
        )

    async def submit_job(
        self, request_body: RequestBody, endpoint: str, job_id: str | None = None
    ) -> ResponseBody:
        """POST the job to RescueBox and return the normalized response body."""
        api_endpoint = f"{'' if endpoint.startswith('/') else '/'}{endpoint}"
        request_dict = {
            "inputs": {
                k: v.model_dump(mode="json") if hasattr(v, "model_dump") else v
                for k, v in request_body.inputs.items()
            },
            "parameters": request_body.parameters,
        }
        return await submit_job_orchestrator(
            self.api,
            self.api_client,
            self.config,
            request_dict,
            api_endpoint,
            job_id,
        )

    async def call_granite_model(
        self, prompt: str, use_advanced: bool = True, update_status_callback=None
    ):
        """Backward-compatible alias for :meth:`call_granite_model_direct` (Ollama-backed)."""
        return await self.call_granite_model_direct(
            prompt,
            use_advanced=use_advanced,
            update_status_callback=update_status_callback,
        )

    async def call_granite_model_direct(
        self, prompt: str, use_advanced: bool = True, update_status_callback=None
    ):
        """Call Granite model via Ollama API for tool selection."""
        return await self._call_ollama(prompt, use_advanced, update_status_callback)

    async def _call_ollama(
        self, prompt: str, use_advanced: bool, update_status_callback=None
    ) -> list | None:
        """Call Ollama API for Granite model tool selection."""
        if update_status_callback:
            update_status_callback("RescueBox working with AI model...")
        _preview = prompt if len(prompt) <= 1200 else prompt[:1200] + "…"
        logger.info(
            "Granite tool selection request: url=%s model=%s use_advanced=%s prompt_len=%d prompt_preview=%r",
            f"{self.ollama_url}/api/chat",
            self.config.GRANITE_MODEL,
            use_advanced,
            len(prompt),
            _preview,
        )
        try:
            if use_advanced:
                messages = create_advanced_granite_prompt(prompt)
                ollama_messages = []
                for m in messages:
                    role = m.get("role", "user")
                    content = m.get("content", "")
                    if m.get("tool_calls"):
                        parts = [content] if content else []
                        for tc in m["tool_calls"]:
                            fn = tc.get("function", tc)
                            name = fn.get("name") if isinstance(fn, dict) else fn
                            args = (
                                fn.get("arguments", {}) if isinstance(fn, dict) else {}
                            )
                            parts.append(
                                f"<tool_code>{json.dumps({'name': name, 'arguments': args})}</tool_code>"
                            )
                        content = "\n".join(parts)
                    ollama_messages.append({"role": role, "content": content})
            else:
                ollama_messages = [
                    {
                        "role": "system",
                        "content": "You are a forensic assistant. Respond with tool calls in <tool_code> tags.",
                    },
                    {"role": "user", "content": prompt},
                ]
            resp = await self.ollama_client.post(
                url=f"{self.ollama_url}/api/chat",
                json={
                    "model": self.config.GRANITE_MODEL,
                    "messages": ollama_messages,
                    "stream": False,
                },
                timeout=600.0,
            )
            if resp.status_code != 200:
                logger.warning(
                    "Ollama failed: %s %s", resp.status_code, resp.text[:200]
                )
                return None
            data = resp.json()
            model_text = data.get("message", {}).get("content", "")
            if model_text:
                logger.debug(
                    "Granite raw response preview (first 800 chars): %s",
                    model_text[:800] + ("…" if len(model_text) > 800 else ""),
                )
                result = parse_fine_tune_tool_response(model_text)
                if result:
                    names = [tc.get("name") for tc in result if isinstance(tc, dict)]
                    logger.info(
                        "Granite tool selection result: parsed_tool_count=%d selected_tools=%s",
                        len(result),
                        names,
                    )
                    return result
                logger.warning(
                    "Granite returned text but no parseable tool calls; preview=%r",
                    model_text[:500],
                )
            else:
                logger.warning("Granite /api/chat returned empty message.content")
        except CHATBOT_ERRORS as e:
            logger.error("Ollama connection or parsing error: %s", e, exc_info=True)
        return None

    async def close(self):
        """Close HTTP clients used by the chatbot core."""
        await self.api.aclose()
        await self.ollama_client.aclose()
