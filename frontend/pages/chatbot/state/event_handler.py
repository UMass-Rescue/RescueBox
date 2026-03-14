"""
Chatbot Event Handler

This module provides the ChatbotEventHandler class for managing UI events
and coordinating callbacks in the chatbot interface.
"""

import logging
from typing import Callable, Optional, Any
from frontend.chatbot.config import ToolRegistry

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ChatbotEventHandler:
    """
    Coordinates UI events and callbacks for the chatbot interface.

    This class manages all UI event handlers and provides a clean interface
    for binding events to UI components.

    Attributes:
        state_manager: Reference to the state manager
        ui_components: Dictionary of UI component references
        callbacks: Dictionary of callback functions
    """

    def __init__(self, state_manager, ui_components: Optional[dict] = None):
        """
        Initialize the event handler.

        Args:
            state_manager: ChatbotStateManager instance
            ui_components: Dictionary of UI component references
        """
        self.state_manager = state_manager
        self.ui_components = ui_components or {}
        self.callbacks = {}

        # Default callbacks that will be set later
        self._send_callback = None

        logger.debug("ChatbotEventHandler initialized")

    def set_callbacks(self,
                     send_callback: Callable = None):
        """
        Set the callback functions for UI events.

        Args:
            send_callback: Callback for send button/message sending
        """
        self._send_callback = send_callback

        logger.debug("Event callbacks configured")

    def set_ui_components(self, **components):
        """
        Set UI component references.

        Args:
            **components: Keyword arguments of component references
        """
        self.ui_components.update(components)
        logger.debug("UI components updated: %s", list(components.keys()))

    def bind_events(self):
        """Bind all event handlers to their respective UI components."""
        logger.debug("Binding event handlers to UI components")

        # Bind input field events
        if 'input_field' in self.ui_components:
            input_field = self.ui_components['input_field']
            input_field.on('keydown', self._handle_input_keydown)

        # Bind button events
        if 'send_button' in self.ui_components and self._send_callback:
            self.ui_components['send_button'].on_click(self._send_callback)




    async def _handle_input_keydown(self, event):
        """
        Handle input field keydown events.

        Args:
            event: NiceGUI event object
        """
        # Extract key information from NiceGUI event
        # In NiceGUI, keyboard event data is available in event.args
        if hasattr(event, 'args') and event.args:
            key = event.args.get('key')
            shift_key = event.args.get('shiftKey', False)

            if key == 'Enter' and not shift_key:
                if hasattr(event, 'preventDefault'):
                    event.preventDefault()
                if self._send_callback and not self.state_manager.is_processing:
                    await self._send_callback()
        else:
            # Fallback for unexpected event structure
            logger.warning("Unexpected event structure in _handle_input_keydown: %s", type(event))

    async def handle_send_message(self):
        """Handle send message event."""
        if self._send_callback:
            await self._send_callback()




    def get_event_status(self) -> dict:
        """
        Get the current status of event bindings.

        Returns:
            dict: Status information about bound events
        """
        return {
            'callbacks_configured': sum(1 for cb in [self._send_callback] if cb is not None),
            'ui_components_bound': len(self.ui_components),
            'state_manager_connected': self.state_manager is not None
        }
