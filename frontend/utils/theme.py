"""
Theme Management Utilities

This module provides utilities for managing theme (light/dark mode) using NiceGUI's
dark mode API and user preferences storage.

Usage:
    from frontend.utils.theme import apply_saved_theme, toggle_theme, create_theme_toggle
    
    # Apply saved theme on page load
    apply_saved_theme()
    
    # Create a theme toggle switch
    theme_toggle = create_theme_toggle()
"""

import logging
from nicegui import ui, app

from frontend.config import APP_DARK_MODE

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def create_theme_toggle():
    """Creates a theme toggle switch that persists the state."""
    try:
        def toggle_dark_mode(e):
            """Event handler to toggle dark mode and save preference."""
            is_dark = e.value
            app.storage.user['dark_mode'] = is_dark
            if is_dark:
                # CORRECT: Call enable() on the instance from ui.dark_mode()
                ui.dark_mode().enable()
            else:
                # CORRECT: Call disable() on the instance from ui.dark_mode()
                ui.dark_mode().disable()
            # Optional: Reload to ensure all components update, though often not needed
            # ui.navigate.reload()

        # Get initial value from user storage
        initial_dark_mode = app.storage.user.get('dark_mode', False)

        # Create the switch
        toggle = ui.switch(
            'Dark Mode',
            value=initial_dark_mode,
            on_change=toggle_dark_mode
        )
        return toggle
    except Exception as e:
        logger.error("Error creating theme toggle: %s", str(e))
        # Return a disabled placeholder to prevent crashing the app
        return ui.switch('Theme Error', value=False).props('disable')


def apply_saved_theme():
    """Apply theme: default is light unless RESCUEBOX_DARK_MODE=true.

    The navbar dark-mode toggle was removed; a stale ``dark_mode`` flag in
    user storage could still force dark UI—clear it when app default is light.
    """
    try:
        if APP_DARK_MODE:
            app.storage.user['dark_mode'] = True
            ui.dark_mode().enable()
            return
        app.storage.user['dark_mode'] = False
        ui.dark_mode().disable()
    except Exception as e:
        logger.warning("Could not apply saved theme: %s", str(e))