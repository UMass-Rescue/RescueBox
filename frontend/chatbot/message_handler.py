# frontend/chatbot/message_handler.py
"""
Message Routing and Handling Logic

This module contains the MessageHandler class which routes user messages to
appropriate handlers based on the input method (slash command vs natural language).

The handler supports multiple input methods:
- Slash commands: Direct tool selection (e.g., /transcribe)
- Smart analyze: Natural language processing via Granite model
"""

import logging
from typing import Dict, Any
from pathlib import Path
from frontend.chatbot.config import ToolRegistry, ChatbotConfig
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.utils import (
    normalize_arguments,
    is_rescuebox_request,
    get_rejection_message,
)

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MessageHandler:
    """
    Handles message routing and tool selection.

    This class is responsible for processing user messages and routing them to
    the appropriate handler based on the input method. It supports slash commands
    for direct tool access and smart analyze for natural language understanding.

    Usage:
        config = ChatbotConfig()
        core = ChatbotCore(config)
        handler = MessageHandler(core, config)
        result = await handler.handle_message(user_input)

    Tips:
    - Messages starting with '/' are treated as slash commands
    - All other messages use smart analyze (Granite model)
    - Input filtering is applied when FILTER_ENABLED is True
    """

    def __init__(self, core: ChatbotCore, config: ChatbotConfig):
        """
        Initialize MessageHandler with core and config.

        Args:
            core (ChatbotCore): Core instance for API and model operations
            config (ChatbotConfig): Configuration including filter settings
        """
        logger.debug("Initializing MessageHandler")
        self.core = core
        self.config = config
        self.tool_registry = ToolRegistry()
        logger.debug("MessageHandler initialized successfully")

    def detect_input_method(self, user_input: str) -> str:
        """
        Detect which input method the user is using.

        This method determines whether the user input is a slash command (starts with '/')
        or natural language that should be processed by smart analyze.

        """
        logger.debug("Detecting input method for input (length=%d)", len(user_input))
        user_input = user_input.strip()

        if user_input.startswith("/"):
            logger.debug("Input method detected: slash_command")
            return "slash_command"
        else:
            logger.debug("Input method detected: smart_analyze")
            return "smart_analyze"

    async def handle_message(
        self, user_input: str, update_status_callback=None
    ) -> Dict[str, Any]:
        """
        Route message to appropriate handler based on input method.

        This is the main entry point for processing user messages. It detects
        the input method and routes to the appropriate handler (slash command
        or smart analyze).

        """
        if update_status_callback:
            update_status_callback("🔍 Analyzing your request...")
        logger.debug("Handling user message (length=%d)", len(user_input))
        method = self.detect_input_method(user_input)
        logger.debug("Routing to handler: %s", method)

        if method == "slash_command":
            return await self.handle_slash_command(user_input, update_status_callback)
        else:
            return await self.handle_smart_analyze(user_input, update_status_callback)

    async def handle_slash_command(
        self, user_input: str, update_status_callback=None
    ) -> Dict[str, Any]:
        """
        Handle slash commands (/help, /models, /assistant, mapped tools).

        Commands are lowercase; payload after the first space is args.
        `/assistant` with no args opens the analysis picker; with args it runs smart analyze after optional filtering.
        """
        logger.debug("Handling slash command: %s", user_input[:50])
        parts = user_input.split(" ", 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        logger.debug("Parsed command: '%s', args length: %d", command, len(args))

        if command == "/help":
            logger.debug("Returning help text")
            return {"type": "help", "content": self.tool_registry.get_help_text()}

        if command == "/models":
            logger.debug("Returning model picker request")
            return {"type": "tool_picker", "content": None}

        if command == "/assistant":
            logger.debug("Processing /assistant command")
            # No args: analysis type picker only
            if not args:
                logger.debug("No args provided, showing analysis picker")
                return {"type": "analysis_picker", "content": None}
            # With args: optional filter then smart analyze
            is_valid, reason = is_rescuebox_request(args, self.config.FILTER_ENABLED)
            if not is_valid:
                logger.warning("Input filtered by /assistant: %s", reason)
                return {"type": "message", "content": get_rejection_message(reason)}
            logger.debug("Routing /assistant to smart analyze handler")
            return await self.handle_smart_analyze(args)

        if command in self.tool_registry.SLASH_COMMANDS:
            endpoint = self.tool_registry.SLASH_COMMANDS[command]
            logger.debug("Slash command '%s' maps to endpoint: %s", command, endpoint)
            return {"type": "show_form", "endpoint": endpoint, "arguments": {}}
        else:
            logger.warning("Unknown slash command: %s", command)
            return {
                "type": "error",
                "content": f"Unknown command: {command}. Type `/help` for available commands.",
            }

    async def handle_smart_analyze(
        self, user_message: str, update_status_callback=None
    ) -> Dict[str, Any]:
        """
        Handle smart analyze using Granite model for tool selection.

        This method processes natural language input by calling the Granite model
        to determine the appropriate tool and parameters. It includes optional
        input filtering to reject non-forensic requests.
        """
        if update_status_callback:
            update_status_callback("🔍 Analyzing your request...")
        logger.debug(
            "Handling smart analyze for message (length=%d)", len(user_message)
        )
        logger.debug("Message preview: %s...", user_message[:100])

        # TODO: trim file/output filter from  user_message

        # Filter check if enabled
        if self.config.FILTER_ENABLED:
            if update_status_callback:
                update_status_callback("🔍 Validating request...")
            logger.debug("Input filtering enabled, checking request validity")
            is_valid, reason = is_rescuebox_request(user_message, True)
            if not is_valid:
                logger.warning("Smart analyze request filtered: %s", reason)
                return {"type": "message", "content": get_rejection_message(reason)}
            if update_status_callback:
                update_status_callback("✅ Request validated")
            logger.debug("Request passed filtering: %s", reason)

        # Call Granite model to get tool call(s)
        if update_status_callback:
            update_status_callback("🤖 AI analyzing request...")
        _p = user_message if len(user_message) <= 2000 else user_message[:2000] + "…"
        logger.debug(
            "Smart analyze: calling Granite for tool selection (prompt_len=%d prompt=%r)",
            len(user_message),
            _p,
        )
        tool_calls = await self.core.call_granite_model_direct(
            user_message, update_status_callback=update_status_callback
        )

        if not tool_calls:
            logger.warning("Granite model did not return any tool calls")
            return {
                "type": "message",
                "content": "⚠️ Could not determine the appropriate tool. "
                "Try being more specific or use `/models` to see all available models.",
            }
        else:
            logger.info("Granite model returned %s tool call(s)", tool_calls)

        # Ensure tool_calls is a list (backward compatibility)
        if not isinstance(tool_calls, list):
            tool_calls = [tool_calls]

        logger.info("Granite model returned %d tool call(s)", len(tool_calls))

        # Validate all tool calls
        validated_calls = []
        for i, tool_call in enumerate(tool_calls):
            endpoint = tool_call.get("name", "")
            if not endpoint:
                logger.warning("Tool call %d missing endpoint name, skipping", i + 1)
                continue

            arguments = tool_call.get("arguments", {})
            # Normalize arguments to match API expectations
            arguments = normalize_arguments(arguments, endpoint)
            validated_calls.append({"endpoint": endpoint, "arguments": arguments})
            logger.debug(
                "Tool call %d: endpoint=%s, args_count=%d",
                i + 1,
                endpoint,
                len(arguments),
            )

        if not validated_calls:
            logger.error("No valid tool calls found")
            return {
                "type": "error",
                "content": "No valid tool calls found in model response",
            }

        logger.debug(
            "Smart analyze: validated endpoints after Granite: %s",
            [c["endpoint"] for c in validated_calls],
        )

        # Try to detect and resolve any input/output filters referenced by the tool calls.
        # Resolve but do not persist by default (persist_if_requested=False). Persisting should
        # only happen when UI/user requests saving filters.
        try:
            from frontend.database.file_filter_utils import process_prompt_for_filters

            try:
                from frontend.utils import get_user_id

                owner = get_user_id()
            except Exception:
                owner = None

            for call in validated_calls:
                input_dir_arg = call["arguments"].get("input_dir") or call[
                    "arguments"
                ].get("input")
                input_dir_path = None
                try:
                    if input_dir_arg:
                        input_dir_path = Path(input_dir_arg)
                except Exception:
                    input_dir_path = None
                try:
                    filter_id = process_prompt_for_filters(
                        user_message,
                        call,
                        input_dir=input_dir_path,
                        owner_id=owner,
                        persist_if_requested=True,
                    )
                    if filter_id:
                        call["_resolved_filter_id"] = filter_id
                        # also propagate into arguments so forms receive the filterId
                        try:
                            call["arguments"]["filterId"] = filter_id
                        except Exception:
                            pass
                except Exception as _e:
                    logger.debug(
                        "process_prompt_for_filters failed for call %s: %s",
                        call.get("endpoint"),
                        _e,
                    )
        except Exception as e:
            logger.debug("Filter resolution skipped or failed: %s", e)
        # If single tool call, return show_form (backward compatible)
        if len(validated_calls) == 1:
            call = validated_calls[0]
            logger.debug("Single tool call: endpoint=%s", call["endpoint"])
            return {
                "type": "show_form",
                "endpoint": call["endpoint"],
                "arguments": call["arguments"],
            }

        # Multiple tool calls - return multi_tool_calls type
        logger.debug("Multiple tool calls detected: %d calls", len(validated_calls))
        return {"type": "multi_tool_calls", "tool_calls": validated_calls}
