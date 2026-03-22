import logging
from nicegui import ui
from typing import Callable, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_chat_header(on_new_conversation: Callable, ui_state: dict, ui_styling: Any = None, on_show_history: Callable = None):
    """
    Create the chat header row used by ChatUIBuilder.

    Returns a tuple of (mode_indicator, models_btn, analyze_btn)
    """
    mode_indicator = None
    models_btn = None
    analyze_btn = None

    with ui.row().classes('bg-white border-b shadow-sm items-center justify-between w-full px-4 py-3 sticky top-0 z-10'):
        # Left side - Title and status
        with ui.row().classes('items-center gap-3'):
            ui.icon('smart_toy', size='1.5rem').classes('text-blue-600')
            # ui.label('🤖 Assistant').classes('text-lg font-semibold text-gray-800 mr-2')
            ui.label('RescueBox Assistant').classes('text-sm text-gray-600')
            # Mode indicator
            mode_indicator = ui.badge('Assistant', color='green').classes('text-xs')

        # Right side - Action buttons
        with ui.row().classes('items-center gap-3'):
            models_btn = ui.button('📋 Models').classes('bg-blue-500 text-white px-4 py-2 rounded-lg')
            analyze_btn = ui.button('🧠 Assistant').classes('bg-blue-500 text-white px-4 py-2 rounded-lg')
            if on_show_history:
                ui.button('📜 History', on_click=on_show_history).classes('bg-gray-200')
            else:
                # Fallback: inform user that history is unavailable
                ui.button('📜 History', on_click=lambda: ui.notify('No history available', type='info')).classes('bg-gray-200')
            ui.button('New Conversation', on_click=on_new_conversation).classes('bg-blue-600 text-white')

    return mode_indicator, models_btn, analyze_btn

