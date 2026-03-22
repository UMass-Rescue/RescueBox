"""
Callback Manager.

Manages and provides standardized callbacks to reduce parameter passing complexity.
"""

from typing import Dict


class CallbackManager:
    """Manages and provides standardized callbacks to reduce parameter passing complexity."""

    def __init__(self, chatbot_page):
        """
        Initialize callback manager with reference to chatbot page.

        Args:
            chatbot_page: Reference to the ChatbotPage instance
        """
        self.chatbot_page = chatbot_page
        self._callbacks = {}

    def get_standard_callbacks(self) -> dict:
        """Return standardized callback dictionary."""
        if not self._callbacks:
            self._callbacks = {
                'add_message': self.chatbot_page._add_message,
                'show_error': self.chatbot_page._show_error,
                'update_status': self.chatbot_page._update_status,
                'load_form': self.chatbot_page.load_and_show_form,
                'process_result': self.chatbot_page._process_result,
                'scroll_to_bottom': self.chatbot_page._scroll_to_bottom,
                'rerun_tool': self.chatbot_page._re_run_tool,
            }
        return self._callbacks

    def get_message_processor_callbacks(self) -> dict:
        """Return callbacks needed for message processing."""
        callbacks = self.get_standard_callbacks()
        return {
            'add_message_callback': callbacks['add_message'],
            'process_result_callback': callbacks['process_result'],
            'show_error_callback': callbacks['show_error'],
            'update_status_callback': callbacks['update_status'],
        }

    def get_result_processor_callbacks(self) -> dict:
        """Return callbacks needed for result processing."""
        callbacks = self.get_standard_callbacks()
        sm = getattr(self.chatbot_page, 'state_manager', None)
        return {
            'add_message_callback': callbacks['add_message'],
            'show_error_callback': callbacks['show_error'],
            'update_status_callback': callbacks['update_status'],
            'load_form_callback': callbacks['load_form'],
            'set_input_enabled_callback': (lambda enabled: sm.set_input_enabled(enabled)) if sm else None,
        }

    def get_form_handler_callbacks(self) -> dict:
        """Return callbacks needed for form handling."""
        callbacks = self.get_standard_callbacks()
        return {
            'show_error_callback': callbacks['show_error'],
            'update_status_callback': callbacks['update_status'],
            'scroll_to_bottom_callback': callbacks['scroll_to_bottom'],
        }
