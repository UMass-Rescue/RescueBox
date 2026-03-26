"""
Unit tests for chatbot configuration and tool registry.

This module tests the configuration management and tool registry systems
that power RescueBox's chatbot capabilities. It validates the core settings
that control AI model connections, tool availability, and user interaction
patterns.

The tests cover:
- Chatbot configuration with default and custom settings
- Tool registry functionality including slash commands
- Tool menu structure and organization
- Fallback endpoint mappings
- Content filtering patterns and keywords
- Help text generation and completeness

These components are critical for ensuring consistent, reliable chatbot
behavior and providing users with clear, discoverable tool access patterns.
"""

import pytest
from frontend.chatbot.config import ChatbotConfig, ToolRegistry

# Configuration constants
DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_GRANITE_MODEL = "granite4:micro"
DEFAULT_RESCUEBOX_HOST = "http://localhost:8000"
DEFAULT_TIMEOUT = 300
DEFAULT_FILTER_ENABLED = True

CUSTOM_OLLAMA_HOST = "http://custom:11434"
CUSTOM_GRANITE_MODEL = "custom-model"
CUSTOM_RESCUEBOX_HOST = "http://custom:8000"
CUSTOM_TIMEOUT = 600
CUSTOM_FILTER_ENABLED = False

# Tool registry constants
TRANSCRIBE_COMMAND = "/transcribe"
DESCRIBE_IMAGES_COMMAND = "/describe-images"
DETECT_DEEPFAKES_COMMAND = "/detect-deepfakes"
AGE_GENDER_COMMAND = "/age-gender"
MODELS_COMMAND = "/models"
ASSISTANT_COMMAND = "/assistant"
HELP_COMMAND = "/help"
SUMMARIZE_COMMAND = "/summarize"

TRANSCRIBE_ENDPOINT = "audio/transcribe"
SUMMARIZE_ENDPOINT = "text_summarization/summarize"
PICK_TOOL_ENDPOINT = "pick_tool"
SMART_ANALYZE_ENDPOINT = "smart_analyze"

TOOL_MENU_KEY_1 = "1"
TOOL_MENU_KEY_7 = "7"

# Help text constants
RESCUEBOX_ASSISTANT_TEXT = "RescueBox Assistant"
SLASH_COMMANDS_TEXT = "Shortcut Commands"
NATURAL_LANGUAGE_TEXT = "Natural Language"
THREE_WAYS_TEXT = "Three different ways"

# Content filtering constants
WEATHER_PATTERN = "weather"
STOCK_PATTERN = "stock"

# Keywords
TRANSCRIBE_KEYWORD = "transcribe"
FORENSIC_KEYWORD = "forensic"
ANALYZE_KEYWORD = "analyze"


class TestChatbotConfig:
    """Tests for ChatbotConfig class and configuration management.

    This class validates the chatbot configuration system that manages
    connections to AI models, RescueBox services, and behavioral settings.
    It ensures that both default and custom configurations work correctly
    and that all required settings are properly initialized.

    Configuration aspects tested:
    - Default configuration values for development/production
    - Custom configuration override capabilities
    - Timeout and connection settings
    - Content filtering enablement
    - Model and service endpoint configuration
    """
    
    def test_default_config(self):
        """Test default configuration values.

        Validates that the ChatbotConfig initializes with sensible defaults
        suitable for development and local deployment scenarios, ensuring
        out-of-the-box functionality without requiring manual configuration.
        """
        config = ChatbotConfig()
        assert config.OLLAMA_HOST == DEFAULT_OLLAMA_HOST
        assert config.GRANITE_MODEL == DEFAULT_GRANITE_MODEL
        # Allow environment override (API_BASE_URL) when running integration-enabled test runs.
        import os
        expected_hosts = {DEFAULT_RESCUEBOX_HOST, os.getenv("API_BASE_URL")} - {None}
        assert config.RESCUEBOX_HOST in expected_hosts
        assert config.TIMEOUT == DEFAULT_TIMEOUT
        assert config.FILTER_ENABLED is DEFAULT_FILTER_ENABLED

    def test_custom_config(self):
        """Test custom configuration values.

        Ensures that all configuration parameters can be properly overridden
        to support different deployment environments, custom model setups,
        and specialized service configurations.
        """
        config = ChatbotConfig(
            OLLAMA_HOST=CUSTOM_OLLAMA_HOST,
            GRANITE_MODEL=CUSTOM_GRANITE_MODEL,
            RESCUEBOX_HOST=CUSTOM_RESCUEBOX_HOST,
            TIMEOUT=CUSTOM_TIMEOUT,
            FILTER_ENABLED=CUSTOM_FILTER_ENABLED
        )
        assert config.OLLAMA_HOST == CUSTOM_OLLAMA_HOST
        assert config.GRANITE_MODEL == CUSTOM_GRANITE_MODEL
        assert config.RESCUEBOX_HOST == CUSTOM_RESCUEBOX_HOST
        assert config.TIMEOUT == CUSTOM_TIMEOUT
        assert config.FILTER_ENABLED is CUSTOM_FILTER_ENABLED


class TestToolRegistry:
    """Tests for ToolRegistry class and tool management system.

    This class validates the tool registry that manages RescueBox's
    available tools, user interaction patterns, and content filtering.
    It ensures that all tools are properly registered, accessible via
    multiple interfaces, and appropriately filtered for safety.

    Tool registry aspects tested:
    - Slash command definitions and endpoint mappings
    - Tool menu structure and organization
    - Fallback endpoint handling
    - Content filtering patterns
    - Keyword-based tool discovery
    - Help text generation and completeness
    - Menu consistency and validation
    """
    
    def test_slash_commands_exist(self):
        """Test that all essential slash commands are defined.

        Validates that the core RescueBox tools are accessible via
        slash commands, providing users with direct, predictable access
        to key functionality through the command interface.
        """
        assert TRANSCRIBE_COMMAND in ToolRegistry.SLASH_COMMANDS
        assert DESCRIBE_IMAGES_COMMAND in ToolRegistry.SLASH_COMMANDS
        assert DETECT_DEEPFAKES_COMMAND in ToolRegistry.SLASH_COMMANDS
        assert AGE_GENDER_COMMAND in ToolRegistry.SLASH_COMMANDS
        assert MODELS_COMMAND in ToolRegistry.SLASH_COMMANDS
        assert ASSISTANT_COMMAND in ToolRegistry.SLASH_COMMANDS
        assert HELP_COMMAND in ToolRegistry.SLASH_COMMANDS

    def test_slash_command_endpoints(self):
        """Test that slash commands map to correct endpoints.

        Ensures that slash commands are properly routed to their
        corresponding API endpoints, maintaining the connection between
        user commands and backend service calls.
        """
        assert ToolRegistry.SLASH_COMMANDS[TRANSCRIBE_COMMAND] == TRANSCRIBE_ENDPOINT
        assert ToolRegistry.SLASH_COMMANDS[SUMMARIZE_COMMAND] == SUMMARIZE_ENDPOINT
        assert ToolRegistry.SLASH_COMMANDS[MODELS_COMMAND] == PICK_TOOL_ENDPOINT
        assert ToolRegistry.SLASH_COMMANDS[ASSISTANT_COMMAND] == SMART_ANALYZE_ENDPOINT
    
    def test_tool_menu_structure(self):
        """Test that tool menu has correct structure and required fields.

        Validates that the numbered tool menu provides all necessary
        information for each tool, including user-friendly names,
        API endpoints, and descriptive text for proper UI display.
        """
        assert TOOL_MENU_KEY_1 in ToolRegistry.TOOL_MENU
        assert TOOL_MENU_KEY_7 in ToolRegistry.TOOL_MENU

        tool_1 = ToolRegistry.TOOL_MENU[TOOL_MENU_KEY_1]
        assert "name" in tool_1
        assert "endpoint" in tool_1
        assert "desc" in tool_1
        assert tool_1["endpoint"] == TRANSCRIBE_ENDPOINT
    
    def test_fallback_endpoints(self):
        """Test that fallback endpoints are properly defined.

        Ensures that fallback endpoint mappings exist for graceful
        degradation when primary tool discovery fails, providing
        reliable tool access even in edge cases.
        """
        assert TOOL_MENU_KEY_1 in ToolRegistry.FALLBACK_ENDPOINTS
        assert TOOL_MENU_KEY_7 in ToolRegistry.FALLBACK_ENDPOINTS
        assert ToolRegistry.FALLBACK_ENDPOINTS[TOOL_MENU_KEY_1] == TRANSCRIBE_ENDPOINT
        assert ToolRegistry.FALLBACK_ENDPOINTS[TOOL_MENU_KEY_7] == SUMMARIZE_ENDPOINT

    def test_blocked_patterns(self):
        """Test that blocked patterns are defined for content filtering.

        Validates that inappropriate or unsupported tool requests are
        properly filtered out, ensuring safe and focused tool usage
        within the RescueBox ecosystem.
        """
        assert len(ToolRegistry.BLOCKED_PATTERNS) > 0
        # Check for common blocked patterns
        patterns_str = " ".join(ToolRegistry.BLOCKED_PATTERNS)
        assert WEATHER_PATTERN in patterns_str or STOCK_PATTERN in patterns_str
    
    def test_rescuebox_keywords(self):
        """Test that RescueBox keywords are defined for tool discovery.

        Ensures that natural language processing can identify RescueBox-
        specific tools through keyword matching, enabling intelligent
        tool suggestions and command interpretation.
        """
        assert len(ToolRegistry.RESCUEBOX_KEYWORDS) > 0
        assert TRANSCRIBE_KEYWORD in ToolRegistry.RESCUEBOX_KEYWORDS
        assert FORENSIC_KEYWORD in ToolRegistry.RESCUEBOX_KEYWORDS
        assert ANALYZE_KEYWORD in ToolRegistry.RESCUEBOX_KEYWORDS

    def test_get_help_text(self):
        """Test help text generation and content completeness.

        Validates that the help system provides comprehensive information
        about available tools and interaction methods, ensuring users
        can effectively discover and use RescueBox capabilities.
        """
        help_text = ToolRegistry.get_help_text()
        assert RESCUEBOX_ASSISTANT_TEXT in help_text
        assert SLASH_COMMANDS_TEXT in help_text
        assert TRANSCRIBE_COMMAND in help_text or TRANSCRIBE_KEYWORD in help_text
        assert "natural language" in help_text.lower()
        assert THREE_WAYS_TEXT in help_text
    
    def test_help_text_contains_all_commands(self):
        """Test that help text contains all slash commands"""
        help_text = ToolRegistry.get_help_text()
        for cmd in ToolRegistry.SLASH_COMMANDS.keys():
            if cmd not in ['/models', '/assistant', '/help']:
                assert cmd in help_text or cmd.replace('/', '') in help_text.lower()
    
    def test_tool_menu_consistency(self):
        """Test that tool menu and fallback endpoints are consistent"""
        for tool_num, tool_info in ToolRegistry.TOOL_MENU.items():
            endpoint = tool_info["endpoint"]
            fallback_endpoint = ToolRegistry.FALLBACK_ENDPOINTS.get(tool_num)
            assert endpoint == fallback_endpoint, \
                f"Tool {tool_num} endpoint mismatch: {endpoint} != {fallback_endpoint}"

