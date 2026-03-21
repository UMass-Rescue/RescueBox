from typing import Any, Callable
from nicegui import ui


def create_chat_window() -> Any:
    """
    Create a chat window container with helper to append messages.
    Returns the container element with methods:
      - append_message(role: str, text: str)
    Uses NiceGUI's native clear() for proper container clearing when switching modes.
    """
    container = ui.column().classes('flex-1 overflow-auto p-4 space-y-4 w-full bg-white rounded-lg shadow-sm border')

    def append_message(role: str, text: str):
        # Simple message card: user vs assistant styling
        with ui.card().classes('p-2') as msg_card:
            if role == 'user':
                ui.label(text).classes('text-right text-sm')
            else:
                ui.label(text).classes('text-left text-sm')
        # Ensure appended into main container by adding as child
        container.add(msg_card)

    # Attach helper; use native container.clear() for mode switching
    container.append_message = append_message
    return container

