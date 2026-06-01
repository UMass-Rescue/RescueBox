# frontend/chatbot/core.py
"""
Core Business Logic for Chatbot Operations

This module contains the ChatbotCore class which handles all core chatbot operations
including API interactions, form generation, job submission, and Granite model integration.

Key Responsibilities:
- Fetching task schemas from API endpoints
- Converting tool call arguments to form initial values
- Creating input forms dynamically
- Submitting jobs to the RescueBox API
- Calling Granite model for tool selection
"""
from pathlib import Path
import sys
import json
import httpx

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from frontend.api_client import ApiClient
from frontend.chatbot.api_helpers import fetch_task_schema
from rb.api.models import TaskSchema, RequestBody, ResponseBody
from frontend.chatbot.schema_utils import (
    convert_arguments_to_initial_values as _convert,
)
from frontend.chatbot.forms import create_input_form as _create
from frontend.chatbot.orchestrator import submit_job_orchestrator
from frontend.chatbot.granite import parse_fine_tune_tool_response
from frontend.chatbot.tool_config import create_advanced_granite_prompt
import logging
from typing import Optional, Dict, Any
from nicegui import ui


# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Thin coordinator class (new) that replaces the runtime ChatbotCore symbol.
# Appending instead of editing the original class body keeps history safe while
# updating the public API used by the rest of the codebase/tests.
# ---------------------------------------------------------------------------
class ThinChatbotCore:
    """
    Thin coordinator that delegates to extracted helper modules.
    """

    def __init__(self, config):
        self.config = config
        self.api_client = httpx.AsyncClient(
            base_url=config.RESCUEBOX_HOST, timeout=config.TIMEOUT
        )
        self.ollama_url = config.OLLAMA_HOST
        logger.info("Granite tool OLLAMA_HOST: url=%s", self.ollama_url)

        self.ollama_client = httpx.AsyncClient(base_url=self.ollama_url, timeout=600.0)
        self.api = ApiClient(config.RESCUEBOX_HOST, timeout=config.TIMEOUT)

    async def get_task_schema_from_endpoint(
        self, endpoint: str
    ) -> Optional[TaskSchema]:
        schema_dict = await fetch_task_schema(
            self.api if hasattr(self, "api") else None,
            self.api_client,
            self.config,
            endpoint,
        )
        return TaskSchema(**schema_dict)

    def convert_arguments_to_initial_values(
        self, arguments: Dict[str, Any], task_schema: TaskSchema, endpoint: str = ""
    ) -> Dict[str, Any]:
        return _convert(arguments, task_schema, endpoint)

    async def create_input_form(
        self,
        task_schema: TaskSchema,
        endpoint: str,
        initial_values: Optional[Dict] = None,
        on_submit: callable = None,
        on_cancel: callable = None,
        container: Optional[ui.element] = None,
    ):
        return await _create(
            task_schema,
            endpoint,
            initial_values=initial_values,
            on_submit=on_submit,
            on_cancel=on_cancel,
            container=container,
        )

    async def submit_job(
        self, request_body: RequestBody, endpoint: str
    ) -> ResponseBody:
        api_endpoint = f"{'' if endpoint.startswith('/') else '/'}{endpoint}"
        request_dict = {
            "inputs": {
                k: v.model_dump(mode="json") if hasattr(v, "model_dump") else v
                for k, v in request_body.inputs.items()
            },
            "parameters": request_body.parameters,
        }
        return await submit_job_orchestrator(
            self.api if hasattr(self, "api") else None,
            self.api_client,
            self.config,
            request_dict,
            api_endpoint,
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
    ) -> Optional[list]:
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
                # Convert to Ollama format (role + content; flatten tool_calls into content)
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
        except Exception as e:
            logger.error("Ollama connection or parsing error: %s", e, exc_info=True)
        return None

    async def close(self):
        await self.api_client.aclose()
        if hasattr(self, "api"):
            await self.api.aclose()
        await self.ollama_client.aclose()
        # Legacy attribute for test compatibility
        if hasattr(self, "_llama_model"):
            self._llama_model = None


# Replace the exported symbol so external imports get the new thin coordinator.
ChatbotCore = ThinChatbotCore
