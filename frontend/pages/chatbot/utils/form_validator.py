"""
Form Validator.

Handles form validation and request preparation logic.
"""

import logging
from pathlib import Path
from typing import Optional
from frontend.pages.chatbot.chatbot_message import ChatMessage, render_message


logger = logging.getLogger(__name__)


class FormValidator:
    """Handles form validation and request preparation."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def validate_and_prepare(self, request_body, endpoint: str, state_manager, container):
        """
        Validate request and prepare for submission.

        Args:
            request_body: Request body to validate
            endpoint: API endpoint name
            state_manager: ChatbotStateManager instance
            container: UI container for error display

        Raises:
            ValueError: If validation fails
        """
        self.logger.info("Validating and preparing job submission for endpoint: %s", endpoint)

        # Update UI state
        state_manager.set_processing(True)
        state_manager.set_status("Running job...")

        # Validate request body
        if not self._validate_request_body(request_body):
            self.logger.error("Invalid request body for endpoint: %s", endpoint)
            raise ValueError("Invalid request body")

        # Validate file paths are accessible
        if not await self._validate_file_paths(request_body, container, state_manager):
            raise ValueError("File path validation failed")

        # Log request payload for debugging
        self._log_request_payload(request_body, endpoint)

    def _validate_request_body(self, request_body) -> bool:
        """Validate the request body structure."""
        if isinstance(request_body, dict) and not request_body.get('is_valid', True):
            self.logger.error("Request body validation failed: %s", request_body.get('errors', {}))
            return False
        return True

    async def _validate_file_paths(self, request_body, container, state_manager) -> bool:
        """Validate file paths for Windows 11 environment."""
        try:
            import os
            inputs = request_body.get('inputs', {}) if isinstance(request_body, dict) else {}

            for key, value in inputs.items():
                if isinstance(value, dict) and 'path' in value:
                    path_str = value['path']
                    path = Path(path_str)
                    
                    if not path.exists():
                        self.logger.warning("Path does not exist: %s", path_str)
                        await self._show_path_warning(
                            container,
                            path_str,
                            "Path does not exist on the local system.",
                            state_manager
                        )
                        return False

                    # Windows 11 specific debugging
                    self.logger.info("=== WINDOWS PATH DEBUGGING ===")
                    self.logger.info("Path: %s | Absolute: %s | OS: %s", path_str, path.is_absolute(), os.name)

                    if path.exists():
                        try:
                            self.logger.info("Permissions - R:%s W:%s X:%s", 
                                            os.access(path, os.R_OK), 
                                            os.access(path, os.W_OK), 
                                            os.access(path, os.X_OK))
                        except Exception as e:
                            self.logger.warning("Permission check failed: %s", str(e))

            return True
        except Exception as e:
            self.logger.error("Error validating file paths: %s", str(e))
            return True

    async def _show_path_warning(self, container, path: str, message: str, state_manager):
        """Show path warning in the chat container."""
        warning_message = ChatMessage(
            'assistant',
            f'⚠️ **Path Warning**: `{path}`\n\n{message}\n\n'
            '🔧 **Note**: Ensure the backend service has permissions to access this Windows path.'
        )
        render_message(container, warning_message)
        state_manager.set_status("Path validation warning")

    def _log_request_payload(self, request_body, endpoint: str):
        """Log the request payload being sent to backend."""
        self.logger.info("=== FINAL REQUEST PAYLOAD TO BACKEND ===")
        self.logger.info("Endpoint: %s", endpoint)
        self.logger.info("Request body: %s", request_body)
        if hasattr(request_body, 'inputs') and request_body.inputs:
            for key, value in request_body.inputs.items():
                if hasattr(value, 'root') and hasattr(value.root, 'path'):
                    self.logger.info("Input %s path: %s", key, value.root.path)
        self.logger.info("=== END REQUEST PAYLOAD ===")
