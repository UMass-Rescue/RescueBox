import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from frontend.chatbot.tool_config import create_advanced_granite_prompt

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _create_fine_tune_granite_prompt(prompt: str) -> list[dict[str, str]]:
    system_message = (
        "You are a forensic analysis assistant for RescueBox."
        "When you need to use a tool, respond with a JSON object inside `<tool_code>` tags. "
    )
    properties = {}
    properties["input_dir"] = {"type": "string", "description": "Path to the input directory"}

    tool = {
            "type": "function",
            "function": {
                "name": "audio/transcribe",
                "description":  "A forensic model to transcribe audio files.",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": ["input_dir"],
                },
            },
        }
    tools_json_str = json.dumps([tool])
    system_content = f"{system_message} <tools>{tools_json_str}</tools>"

    system_message = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": prompt}
    ]
    return system_message


def parse_fine_tune_tool_response(model_text: str) -> Optional[List[Dict[str, Any]]]:
    import re
    tool_calls = []

    pattern = r'<tool_code>\s*(\{.*?\})\s*</tool_code>'
    matches = re.findall(pattern, model_text, re.DOTALL)
    if matches:
        logger.info("Found %d tool call(s) in <tool_code> tags", len(matches))
        for tool_call_json in matches:
            try:
                tool_call = json.loads(tool_call_json)
                tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue
        if tool_calls:
            return tool_calls

    json_pattern = r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^}]*\}\s*\}'
    json_matches = re.findall(json_pattern, model_text, re.DOTALL)
    if json_matches:
        for json_str in json_matches:
            try:
                tool_call = json.loads(json_str)
                if 'name' in tool_call and 'arguments' in tool_call:
                    tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue
        if tool_calls:
            return tool_calls

    logger.warning("No valid tool calls found in fine_tune model response")
    logger.debug("Response text: %s", model_text[:500])
    return None


class GraniteLocal:
    """
    Local Granite model wrapper using llama-cpp-python. Loads model lazily and
    runs inference in a threadpool to avoid blocking the event loop.
    """
    def __init__(self):
        self._llama_model = None
        self._llama_model_path = None

    async def call_direct(self, prompt: str, model_path: str, use_advanced: bool = True, update_status_callback=None):
        import os
        import asyncio
        try:
            if update_status_callback:
                update_status_callback("🧠 Rescuebox working with AI model...")

            try:
                from llama_cpp import Llama, llama_supports_gpu_offload
            except ImportError as e:
                logger.error("llama-cpp-python not installed: %s", e)
                return None

            if self._llama_model is None or self._llama_model_path != model_path:
                model_file = Path(model_path)
                if not model_file.exists():
                    logger.error("RescueBox Granite model gguf file not found: %s", model_path)
                    return None
                loop = asyncio.get_event_loop()
                def load_model():
                    return Llama(
                        model_path=str(model_path),
                        n_gpu_layers=-1,
                        n_ctx=4096,
                        n_threads=os.cpu_count() or 4,
                        verbose=False
                    )
                self._llama_model = await loop.run_in_executor(None, load_model)
                self._llama_model_path = model_path

            loop = asyncio.get_event_loop()
            def run_inference():
                if not use_advanced:
                    messages = _create_fine_tune_granite_prompt(prompt)  
                else:
                    logger.info("Run create_advanced_granite_prompt")
                    messages = create_advanced_granite_prompt(prompt)
                kwargs = {"messages": messages, "max_tokens": 2048, "temperature": 0.1}
                if use_advanced:
                    # advanced formatting handled outside; keep compatibility
                    pass
                return self._llama_model.create_chat_completion(**kwargs)

            model_output = await loop.run_in_executor(None, run_inference)
            if model_output and 'choices' in model_output and len(model_output['choices']) > 0:
                model_text = model_output['choices'][0]['message'].get('content', '')
            else:
                logger.warning("Model returned empty or invalid response")
                return None

            if use_advanced:
                # advanced parsing not implemented here; fallback to fine_tune parser
                return parse_fine_tune_tool_response(model_text)
            return parse_fine_tune_tool_response(model_text)
        except Exception as e:
            logger.error("Error calling Granite model directly: %s", str(e), exc_info=True)
            return None

    def release_model(self) -> None:
        """
        Release references to the loaded llama model to free resources.
        Public method to avoid accessing protected members from other classes.
        """
        try:
            self._llama_model = None
            self._llama_model_path = None
        except Exception:
            # best-effort cleanup; don't raise
            pass
