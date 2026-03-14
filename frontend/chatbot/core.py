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
import httpx
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
from frontend.api_client import ApiClient
from frontend.chatbot.api_helpers import fetch_task_schema
from rb.api.models import TaskSchema, RequestBody, ResponseBody
from frontend.constants import DEFAULT_GRANITE_GGUF_MODEL_PATH
from frontend.chatbot.schema_utils import convert_arguments_to_initial_values as _convert
from frontend.chatbot.forms import create_input_form as _create
from frontend.chatbot.orchestrator import submit_job_orchestrator
from frontend.chatbot.granite import GraniteLocal
import logging
from typing import Optional, Dict, Any



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
        self.api_client = httpx.AsyncClient(base_url=config.RESCUEBOX_HOST, timeout=config.TIMEOUT)
        self.ollama_client = httpx.AsyncClient(base_url=config.OLLAMA_HOST, timeout=60.0)
        self.api = ApiClient(config.RESCUEBOX_HOST, timeout=config.TIMEOUT)
        self._granite_local = None
        # preserve legacy attribute expected by tests
        self._llama_model = None

    async def get_task_schema_from_endpoint(self, endpoint: str) -> Optional[TaskSchema]:
        schema_dict = await fetch_task_schema(self.api if hasattr(self, 'api') else None, self.api_client, self.config, endpoint)
        return TaskSchema(**schema_dict)

    def convert_arguments_to_initial_values(self, arguments: Dict[str, Any], task_schema: TaskSchema, endpoint: str = "") -> Dict[str, Any]:
        return _convert(arguments, task_schema, endpoint)

    async def create_input_form(self, task_schema: TaskSchema, endpoint: str, initial_values: Optional[Dict] = None, on_submit: callable = None):
        return await _create(task_schema, endpoint, initial_values=initial_values, on_submit=on_submit)

    async def submit_job(self, request_body: RequestBody, endpoint: str) -> ResponseBody:
        api_endpoint = f"{'' if endpoint.startswith('/') else '/'}{endpoint}"
        request_dict = {
            'inputs': {k: v.model_dump(mode='json') if hasattr(v, 'model_dump') else v for k, v in request_body.inputs.items()},
            'parameters': request_body.parameters
        }
        return await submit_job_orchestrator(self.api if hasattr(self, 'api') else None, self.api_client, self.config, request_dict, api_endpoint)


    async def call_granite_model_direct(self, prompt: str, model_path: str = DEFAULT_GRANITE_GGUF_MODEL_PATH, use_advanced: bool = True, update_status_callback=None):
        if self._granite_local is None or getattr(self._granite_local, '_llama_model_path', None) != model_path:
            self._granite_local = GraniteLocal()
        result = await self._granite_local.call_direct(prompt, model_path, use_advanced=use_advanced, update_status_callback=update_status_callback)
        # Legacy attribute: set to None or updated via public accessor if available
        # Do not access protected members; keep legacy attribute unset
        self._llama_model = None
        return result

    async def close(self):
        await self.api_client.aclose()
        if hasattr(self, 'api'):
            await self.api.aclose()
        await self.ollama_client.aclose()
        if self._granite_local is not None:
            try:
                releaser = getattr(self._granite_local, 'release_model', None)
                if callable(releaser):
                    releaser()
            except Exception:
                pass
        self._llama_model = None


# Replace the exported symbol so external imports get the new thin coordinator.
ChatbotCore = ThinChatbotCore