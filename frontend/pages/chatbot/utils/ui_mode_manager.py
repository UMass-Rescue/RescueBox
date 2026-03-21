"""
UI Mode Manager

Handles UI mode switching and related operations for different chat modes.
"""

import logging

from frontend.pages.chatbot.utils.ui_operations import UIOperations
from frontend.pages.chatbot.utils.ui_styling import UIStyling


logger = logging.getLogger(__name__)


class UIModeManager:
    """Handles UI mode switching and related operations."""

    def __init__(self, mode_indicator, models_btn, analyze_btn, chat_container,
                 status_text_ref=None, form_submit_handler=None, core=None, state_manager=None):
        """
        Initialize UI mode manager.

        Args:
            mode_indicator: UI element showing current mode
            models_btn: Models mode button
            analyze_btn: Analyze mode button
            chat_container: Chat messages container
            status_text_ref: Status text reference (optional)
            form_submit_handler: Form submit handler (optional)
            core: Chatbot core (optional)
            state_manager: ChatbotStateManager (optional) - cleared when switching modes
        """
        self.mode_indicator = mode_indicator
        self.models_btn = models_btn
        self.analyze_btn = analyze_btn
        self.chat_container = chat_container
        self.status_text_ref = status_text_ref
        self.form_submit_handler = form_submit_handler
        self.core = core
        self.state_manager = state_manager
        self.logger = logging.getLogger(__name__)

    async def switch_mode(self, mode: str, input_area=None):
        """
        Switch between different UI modes.

        Args:
            mode: Mode to switch to ('analyze' or 'models')
            input_area: Input area element (optional)
        """
        # Clear in-memory messages so the new mode shows a clean slate
        if self.state_manager and hasattr(self.state_manager, 'clear_messages'):
            self.state_manager.clear_messages()
            self.logger.debug("Cleared state manager messages when switching to %s mode", mode)
        # Clear chat container when switching modes to remove all UI elements
        self.chat_container.clear()
        self.logger.debug("Cleared chat container when switching to %s mode", mode)

        if mode == 'analyze':
            self.mode_indicator.text = 'Analyze'
            self.mode_indicator.props('color=green')

            # Update button styles
            self.analyze_btn.classes(UIStyling.BUTTON_ENABLED, remove=UIStyling.BUTTON_DISABLED)
            self.models_btn.classes(UIStyling.BUTTON_DISABLED, remove=UIStyling.BUTTON_ENABLED)

            # Show both chat and input if input_area provided
            if input_area is not None:
                self.chat_container.classes('', remove='hidden')
                input_area.classes('', remove='hidden')

        elif mode == 'models':
            self.mode_indicator.text = 'Models'
            self.mode_indicator.props('color=purple')

            # Update button styles
            self.models_btn.classes(UIStyling.BUTTON_ENABLED, remove=UIStyling.BUTTON_DISABLED)
            self.analyze_btn.classes(UIStyling.BUTTON_DISABLED, remove=UIStyling.BUTTON_ENABLED)

            # Show chat, hide input if input_area provided
            if input_area is not None:
                self.chat_container.classes('', remove='hidden')
                input_area.classes('hidden')

        self.logger.info("Switched to %s mode", mode)
        UIOperations.safe_notify(f'Switched to {mode} mode', type='info', timeout=1000)

