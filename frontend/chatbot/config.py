# frontend/chatbot/config.py
"""
Configuration and Tool Registry Module

This module defines the configuration settings and tool registry for the chatbot.
It contains all the mappings between user commands, endpoints, and tool definitions.

IMPORTANT: UPDATE THIS FILE WHEN ADDING NEW TOOLS

To add a new tool:
1. Add entry to SLASH_COMMANDS in config.py
2. Add entry to TOOL_MENU in config.py
3. Optionally add keywords to RESCUEBOX_KEYWORDS
4. Help text updates automatically
The core logic, UI, and message handling remain unchanged when adding new tools.

Key Components:
- ChatbotConfig: Pydantic model for chatbot configuration settings
- ToolRegistry: Static registry of all available tools and their mappings
"""

import logging
import os
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def normalize_ollama_host(raw: str, *, default: str = "http://127.0.0.1:11434") -> str:
    """Return an Ollama API base URL with ``http://`` or ``https://`` (env often omits scheme)."""
    url = (raw or "").strip() or default
    if url != "0.0.0.0" and not url.startswith(("http://", "https://")):
        return f"http://{url}"
    if url == "0.0.0.0":
        return default
    return url


def collect_ollama_model_names(tags_payload: dict) -> List[str]:
    """Collect distinct model ids from an Ollama ``/api/tags`` JSON body."""
    names: List[str] = []
    for entry in tags_payload.get("models") or []:
        for key in ("name", "model"):
            value = (entry.get(key) or "").strip()
            if value and value not in names:
                names.append(value)
    return names


def _normalize_model_id(model_id: str) -> str:
    return (model_id or "").strip().lower().replace(":", "-").replace("_", "-")


def _model_id_root(normalized_id: str) -> str:
    """Drop common Ollama tag suffixes (e.g. ``-latest``) for matching."""
    parts = normalized_id.split("-")
    if len(parts) >= 2 and parts[-1] in ("latest", "main"):
        return "-".join(parts[:-1])
    return normalized_id


def resolve_ollama_model_tag(requested: str, available: List[str]) -> Optional[str]:
    """Map a configured model name to the tag string Ollama expects."""
    req = (requested or "").strip()
    if not req or not available:
        return None

    req_root = _model_id_root(_normalize_model_id(req))
    req_norm = _normalize_model_id(req)

    for candidate in available:
        tag = (candidate or "").strip()
        if not tag:
            continue
        tag_norm = _normalize_model_id(tag)
        tag_root = _model_id_root(tag_norm)
        if tag.lower() == req.lower():
            return tag
        if tag_root == req_root or tag_norm == req_norm:
            return tag
        if req_root and (req_root in tag_norm or tag_root in req_norm):
            return tag

    if "granite" in req.lower():
        for candidate in available:
            tag = (candidate or "").strip()
            if tag and "granite" in tag.lower():
                return tag
    return None


class ChatbotConfig(BaseModel):
    """
    Configuration settings for the chatbot system.
    This Pydantic model defines all configurable parameters for the chatbot,
    including API endpoints, model names, timeouts, and feature flags.
    """

    OLLAMA_HOST: str = Field(
        default="http://127.0.0.1:11434", description="Ollama API base URL"
    )
    GRANITE_MODEL: str = Field(
        default="ibm/granite4.1:3b", description="Granite model name for tool calling"
    )
    RESCUEBOX_HOST: str = Field(
        default="http://localhost:8000", description="RescueBox API base URL"
    )
    TIMEOUT: int = Field(
        default=60 * 60 * 24 * 7, description="HTTP request timeout in seconds"
    )
    FILTER_ENABLED: bool = Field(
        default=True, description="Enable input filtering for non-forensic requests"
    )
    POLL_INTERVAL: float = Field(
        default=5.0,
        description="Polling interval (seconds) for checking running jobs on page load",
    )

    def __init__(self, **data):
        """Initialize ChatbotConfig with logging and allow environment overrides."""
        # Allow environment variables to override defaults when constructing config.
        # Tests may instantiate ChatbotConfig without passing RESCUEBOX_HOST; prefer env var if present.
        env_rescue = os.getenv("RESCUEBOX_HOST")
        # Also allow API_BASE_URL to override RESCUEBOX_HOST (test runner sets this)
        env_api_base = os.getenv("API_BASE_URL")
        env_ollama = os.getenv("OLLAMA_HOST")
        env_granite = os.getenv("GRANITE_MODEL")
        # Respect API_BASE_URL only for integration runs (controlled by RUN_INTEGRATION).
        # This prevents test runs from accidentally inheriting an externally-set API_BASE_URL
        # when unit tests expect the default host.
        run_integration_flag = os.getenv("RUN_INTEGRATION")
        if (
            env_api_base
            and "RESCUEBOX_HOST" not in data
            and run_integration_flag in ("1", "true", "True")
        ):
            data["RESCUEBOX_HOST"] = env_api_base
        elif env_rescue and "RESCUEBOX_HOST" not in data:
            data["RESCUEBOX_HOST"] = env_rescue
        if env_ollama and "OLLAMA_HOST" not in data:
            data["OLLAMA_HOST"] = normalize_ollama_host(env_ollama)
        if env_granite and "GRANITE_MODEL" not in data:
            data["GRANITE_MODEL"] = env_granite

        # Long-running jobs (e.g. image_summary) — override default TIMEOUT without code changes
        if "TIMEOUT" not in data:
            env_job_timeout = os.getenv("RESCUEBOX_CHATBOT_TIMEOUT")
            if env_job_timeout:
                try:
                    data["TIMEOUT"] = int(float(env_job_timeout))
                except ValueError:
                    pass

        super().__init__(**data)
        logger.info(
            "ChatbotConfig initialized: OLLAMA_HOST=%s, RESCUEBOX_HOST=%s, "
            "GRANITE_MODEL=%s, TIMEOUT=%s, FILTER_ENABLED=%s",
            self.OLLAMA_HOST,
            self.RESCUEBOX_HOST,
            self.GRANITE_MODEL,
            self.TIMEOUT,
            self.FILTER_ENABLED,
        )


class ToolRegistry:
    """Tool registry - Add new tools here"""

    # Slash command to endpoint mapping (Method 1: Slash Commands)
    SLASH_COMMANDS: Dict[str, str] = {
        "/transcribe": "audio/transcribe",
        "/describe-images": "image_summary/summarize-images",
        "/detect-deepfakes": "deepfake_detection/predict",
        "/age-gender": "age-gender/predict",
        "/upload-faces": "face-match/bulkupload",
        "/find-faces": "face-match/findfacebulk",
        "/summarize-text": "text_summarization/summarize",
        "/search-text": "text_embeddings/search",
        "/search-images": "image_embeddings/search_images",
        "/similar-images": "image_similarity/search_similar_images",
        "/ufdr-mount": "ufdr_mounter/mount",
        "/models": "pick_tool",
        "/assistant": "smart_analyze",
        "/help": "help",
    }

    # Tool picker menu (Method 4: Tool Picker)
    TOOL_MENU: Dict[str, Dict[str, str]] = {
        "1": {
            "name": "Transcribe Audio",
            "endpoint": "audio/transcribe",
            "desc": "Convert speech to text",
        },
        "2": {
            "name": "Describe Images",
            "endpoint": "image_summary/summarize-images",
            "desc": "AI descriptions of photos",
        },
        "3": {
            "name": "Search Images",
            "endpoint": "image_embeddings/search_images",
            "desc": "description or caption match",
        },
        "4": {
            "name": "Age & Gender Predictor",
            "endpoint": "age-gender/predict",
            "desc": "Classify faces by age and gender",
        },
        "5": {
            "name": "Detect Deepfakes",
            "endpoint": "deepfake_detection/predict",
            "desc": "Find manipulated media",
        },
        "6": {
            "name": "Upload Face Match",
            "endpoint": "face-match/bulkupload",
            "desc": "Step 1 Build face collection",
        },
        "7": {
            "name": "Find Face Match",
            "endpoint": "face-match/findfacebulk",
            "desc": "Step 2 Search face collection",
        },
        "8": {
            "name": "Summarize Text",
            "endpoint": "text_summarization/summarize",
            "desc": "Document summaries",
        },
        "9": {
            "name": "Search Text",
            "endpoint": "text_embeddings/search",
            "desc": "words or caption match",
        },
        "10": {
            "name": "UFDR Mount",
            "endpoint": "ufdr_mounter/mount",
            "desc": "Mount UFDR files",
        },
        "11": {
            "name": "Similar Images",
            "endpoint": "image_similarity/search_similar_images",
            "desc": "Find images similar to a query image",
        },
    }

    @staticmethod
    def tool_menu_name_for_endpoint(endpoint: str) -> Optional[str]:
        """
        Return TOOL_MENU ``name`` (e.g. \"Search Images\") for an API endpoint, or None if not in the menu.
        """
        for tool in ToolRegistry.TOOL_MENU.values():
            if tool["endpoint"] == endpoint:
                return tool["name"]
        return None

    @staticmethod
    def display_name_for_endpoint(endpoint: Optional[str]) -> str:
        """User-facing plugin label for an API route; falls back to the route string."""
        ep = (endpoint or "").strip().lstrip("/")
        if not ep:
            return "plugin"
        return ToolRegistry.tool_menu_name_for_endpoint(ep) or ep

    @staticmethod
    def ordered_plugin_uids() -> List[str]:
        """
        Plugin ``uid`` values (first path segment of each TOOL_MENU endpoint) in tool-picker order.

        Used by ``/models`` so the plugin list matches the chatbot tool menu. Endpoints that share
        a plugin (e.g. ``face-match/...``) appear once, in the position of their first menu entry.
        """
        seen: list[str] = []
        for key in sorted(ToolRegistry.TOOL_MENU.keys(), key=int):
            endpoint = ToolRegistry.TOOL_MENU[key]["endpoint"]
            uid = endpoint.split("/")[0]
            if uid not in seen:
                seen.append(uid)
        return seen

    # Non-forensic chit-chat (applied only after RESCUEBOX_KEYWORDS / path checks in utils.py)
    BLOCKED_PATTERNS: list[str] = [
        r"\b(weather|stock|news|sports|politics)\b",
        r"\b(joke|funny|humor|laugh)\b",
        r"\b(recipe|cook|food|restaurant)\b",
        r"\b(movie|music|game|entertainment)\b",
        r"^(hello|hi|hey|how are you|what's up)[\?\!\.]?$",
        r"\b(who are you|what can you do|help me)\b",
        r"\b(write|compose|create|generate)\b.*(story|poem|essay|code)",
        r"\b(translate|convert)\b.*(language|spanish|french|german)",
    ]

    # Enhanced request filtering keywords (from filter_user_input.py and rescuebox_tool.py)
    RESCUEBOX_KEYWORDS: list[str] = [
        # Audio
        "transcribe",
        "audio",
        "speech",
        "voice",
        "recording",
        "interview",
        # Images
        "image",
        "photo",
        "picture",
        "describe",
        "visual",
        # Age/Gender
        "age",
        "gender",
        "classify",
        "demographics",
        "face",
        # Deepfake
        "deepfake",
        "fake",
        "synthetic",
        "manipulated",
        "authentic",
        "real",
        # Face matching
        "face match",
        "find face",
        "upload face",
        "collection",
        "identify",
        "recognize",
        "suspect",
        "missing person",
        "match",
        # Text
        "summarize",
        "summary",
        "document",
        "text",
        "report",
        # Text embeddings & semantic search
        "embed",
        "embedding",
        "semantic search",
        "vector search",
        "similar text",
        # General forensic
        "forensic",
        "evidence",
        "analyze",
        "analysis",
        "investigate",
        "case",
        "detect",
        "scan",
        "process",
        "extract",
        # UFDR / mobile forensics
        "ufdr",
        "cellebrite",
        # Image embeddings & semantic search
        "image search",
        "vector search",
        "similar image",
        # Common paths (indicator of tool usage)
        "/tmp",
        "/data",
        "/evidence",
        "/home",
        "/case",
        "/images",
    ]

    @staticmethod
    def get_help_text() -> str:
        """
        Generate help text from tool registry.

        This method dynamically builds help documentation by iterating through
        the tool registry. It combines slash commands, tool menu descriptions,
        and usage instructions into a formatted markdown string.

        The help text includes:
        - List of all slash commands with descriptions
        - Special commands (/models, /assistant, /help)
        - Natural language usage examples
        - Overview of available methods

        Returns:
            str: Formatted markdown help text suitable for display in the UI

        Usage:
            help_text = ToolRegistry.get_help_text()
            # Display in UI or send as message

        Tips:
        - Help text is automatically generated, so adding tools to registry
          automatically updates the help
        - Special commands (pick_tool, smart_analyze, help) are excluded from
          the main list but included in the special commands section
        - Descriptions come from TOOL_MENU if available, otherwise uses endpoint name
        """
        logger.info("Generating help text from tool registry")

        # help_text = """### 🛠️ RescueBox Usage

        help_text = """

#### Three different ways to use RescueBox Assistant
1. **Menu Selctor** - **Type `/models`** to see all the plugins and you pick one
2. **Assistant** - Enter a **prompt plugin task in natural language**
-**Transcribe** audio files in /evidence/recordings
or
-**Summarize** photos in /images/case456

The typical workflow sequence is :
  1 you pick a menul plugin or enter a chat prompt and let the assistant select the plugin
  2 a form is displayed with inputs and you fill in the inputs
  3 you submit the job and the assistant runs the job
  4 the results are shown in the jobs page with details
  5 inputs are validated to make sure the input folder path is ok and expected file types are found

Advanced workflow is:
 you type in a prompt that runs a pipeline of plugins and you interact with each after 
 the previous step is complete , 
 for example 
 1 "transcribe and summarize the audio files and search the text summaries for a backpack"
 the assistant will run the transcribe job first, then the summarize job, then the search job
 and you will see the results in the jobs page

2 "detect age and gender of these photos and summarize" will go thru the input folder find faces and set age/gender
for each face in photo and then ask for a filter you would select gender / age and then apply the filter, now 
only the photos that match the filter will be fed to the next step to summarize "


"""

        return help_text
