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
from pydantic import BaseModel, Field
from typing import Dict, Any

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ChatbotConfig(BaseModel):
    """
    Configuration settings for the chatbot system.
    
    This Pydantic model defines all configurable parameters for the chatbot,
    including API endpoints, model names, timeouts, and feature flags.
    
    Attributes:
        OLLAMA_HOST (str): Base URL for Ollama API (default: "http://localhost:11434")
            Used for Granite model inference
        GRANITE_MODEL (str): Name of the fine-tuned Granite model (default: "granite4:micro")
            This model handles tool calling and natural language understanding
        RESCUEBOX_HOST (str): Base URL for RescueBox API (default: "http://localhost:8000")
            Backend API for job submission and schema fetching
        TIMEOUT (int): HTTP request timeout in seconds (default: 300)
            Used for long-running API calls
        FILTER_ENABLED (bool): Enable input filtering (default: True)
            When True, filters out non-forensic requests
    
    Usage:
        # Use defaults
        config = ChatbotConfig()
        
        # Custom configuration
        config = ChatbotConfig(
            OLLAMA_HOST="http://custom-ollama:11434",
            GRANITE_MODEL="custom-model",
            FILTER_ENABLED=False
        )
    
    Tips:
    - Increase TIMEOUT for very long-running operations
    - Set FILTER_ENABLED=False during development for easier testing
    - Ensure OLLAMA_HOST is accessible from the frontend
    - The GRANITE_MODEL must be available in your Ollama instance
    """
    OLLAMA_HOST: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    GRANITE_MODEL: str = Field(default="granite4:micro", description="Granite model name for tool calling")
    RESCUEBOX_HOST: str = Field(default="http://localhost:8000", description="RescueBox API base URL")
    TIMEOUT: int = Field(default=300, description="HTTP request timeout in seconds")
    FILTER_ENABLED: bool = Field(default=True, description="Enable input filtering for non-forensic requests")
    POLL_INTERVAL: float = Field(default=5.0, description="Polling interval (seconds) for checking running jobs on page load")
    
    def __init__(self, **data):
        """Initialize ChatbotConfig with logging and allow environment overrides."""
        # Allow environment variables to override defaults when constructing config.
        # Tests may instantiate ChatbotConfig without passing RESCUEBOX_HOST; prefer env var if present.
        env_rescue = os.getenv('RESCUEBOX_HOST')
        # Also allow API_BASE_URL to override RESCUEBOX_HOST (test runner sets this)
        env_api_base = os.getenv('API_BASE_URL')
        env_ollama = os.getenv('OLLAMA_HOST')
        env_granite = os.getenv('GRANITE_MODEL')
        # Respect API_BASE_URL only for integration runs (controlled by RUN_INTEGRATION).
        # This prevents test runs from accidentally inheriting an externally-set API_BASE_URL
        # when unit tests expect the default host.
        run_integration_flag = os.getenv('RUN_INTEGRATION')
        if env_api_base and 'RESCUEBOX_HOST' not in data and run_integration_flag in ('1', 'true', 'True'):
            data['RESCUEBOX_HOST'] = env_api_base
        elif env_rescue and 'RESCUEBOX_HOST' not in data:
            data['RESCUEBOX_HOST'] = env_rescue
        if env_ollama and 'OLLAMA_HOST' not in data:
            data['OLLAMA_HOST'] = env_ollama
        if env_granite and 'GRANITE_MODEL' not in data:
            data['GRANITE_MODEL'] = env_granite

        super().__init__(**data)
        logger.info("ChatbotConfig initialized: RESCUEBOX_HOST=%s, GRANITE_MODEL=%s, TIMEOUT=%s, FILTER_ENABLED=%s",
                     self.RESCUEBOX_HOST, self.GRANITE_MODEL, self.TIMEOUT, self.FILTER_ENABLED)


class ToolRegistry:
    """Tool registry - Add new tools here"""
    
    # Slash command to endpoint mapping (Method 1: Slash Commands)
    SLASH_COMMANDS: Dict[str, str] = {
        '/transcribe': 'audio/transcribe',
        '/describe-images': 'image_summary/summarize-images',
        '/detect-deepfakes': 'deepfake_detection/predict',
        '/age-gender': 'age-gender/predict',
        '/upload-faces': 'face-match/bulkupload',
        '/find-faces': 'face-match/findfacebulk',
        '/summarize': 'text_summarization/summarize',
        '/search-text': 'text_embeddings/search',
        '/ufdr-mount': 'ufdr_mounter/mount',
        '/models': 'pick_tool',
        '/assistant': 'smart_analyze',
        '/help': 'help',
    }
    
    # Tool picker menu (Method 4: Tool Picker)
    TOOL_MENU: Dict[str, Dict[str, str]] = {
        "1": {"name": "🎤 Transcribe Audio", "endpoint": "audio/transcribe", "desc": "Convert speech to text"},
        "2": {"name": "🖼️ Describe Images", "endpoint": "image_summary/summarize-images", "desc": "AI descriptions of photos"},
        "3": {"name": "👤 Age & Gender", "endpoint": "age-gender/predict", "desc": "Classify faces"},
        "4": {"name": "🔍 Detect Deepfakes", "endpoint": "deepfake_detection/predict", "desc": "Find manipulated media"},
        "5": {"name": "📤 Upload Faces", "endpoint": "face-match/bulkupload", "desc": "Build face collection"},
        "6": {"name": "🔎 Find Faces", "endpoint": "face-match/findfacebulk", "desc": "Search face collection"},
        "7": {"name": "📝 Summarize Text", "endpoint": "text_summarization/summarize", "desc": "Document summaries"},
        "8": {"name": "🔍 Search Text", "endpoint": "text_embeddings/search", "desc": "Semantic search text files"},
        "9": {"name": "🔍 UFDR Mount", "endpoint": "ufdr_mounter/mount", "desc": "Mount UFDR files"},
    }
    
    # Fallback endpoints for tool picker (when Granite model unavailable)
    FALLBACK_ENDPOINTS: Dict[str, str] = {
        "1": "audio/transcribe",
        "2": "image_summary/summarize-images",
        "3": "age-gender/predict",
        "4": "deepfake_detection/predict",
        "5": "face-match/bulkupload",
        "6": "face-match/findfacebulk",
        "7": "text_summarization/summarize",
        "8": "text_embeddings/search",
        "9": "ufdr_mounter/mount",
    }
    
    # Enhanced blocked patterns (non-forensic requests to reject)
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
        "transcribe", "audio", "speech", "voice", "recording", "interview",
        # Images
        "image", "photo", "picture", "describe", "visual",
        # Age/Gender
        "age", "gender", "classify", "demographics", "face",
        # Deepfake
        "deepfake", "fake", "synthetic", "manipulated", "authentic", "real",
        # Face matching
        "face match", "find face", "upload face", "collection", "identify", "recognize",
        "suspect", "missing person", "match",
        # Text
        "summarize", "summary", "document", "text", "report",
        # Text embeddings & semantic search
        "embed", "embedding", "semantic search", "vector search", "similar text",
        # General forensic
        "forensic", "evidence", "analyze", "analysis", "investigate", "case",
        "detect", "scan", "process", "extract",
        # UFDR / mobile forensics
        "ufdr", "cellebrite",
        # Common paths (indicator of tool usage)
        "/tmp", "/data", "/evidence", "/home", "/case",
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
1. **Tool Picker** - **Type `/models`** to see all the plugins and you pick one
2. **Assistant** - Enter a **prompt plugin task in natural language**
-**Transcribe** audio files in /evidence/recordings
or
-**Summarize** photos in /images/case456

3. **Shortcut Commands** - For Advanced users eg. `/transcribe` to transcribe audio files
"""
        #help_text += """#### Shortcut model commands"""
        logger.debug("Processing %d slash commands", len(ToolRegistry.SLASH_COMMANDS))
        
        for cmd, endpoint in ToolRegistry.SLASH_COMMANDS.items():
            if endpoint not in ['pick_tool', 'smart_analyze', 'help']:
                # Get description from tool menu if available
                desc = next(
                    (tool["desc"] for tool in ToolRegistry.TOOL_MENU.values() if tool["endpoint"] == endpoint),
                    endpoint
                )
                help_text += f"- `{cmd}` - {desc}\n"
                logger.debug("Added help entry for %s: %s", cmd, desc)

        logger.info("Help text generated successfully")
        return help_text