from typing import Any, Callable
from nicegui import ui


def render_welcome_message(container: ui.element) -> None:
    """
    Render the standard welcome message into the given container.

    Used by: Open Assistant (initial load), New Conversation, and switching to Assistant mode.
    Keeps all three entry points consistent with the same friendly greeting.
    """
    with container:
        with ui.card().classes('w-full max-w-sm bg-blue-50 shadow-sm'):
            with ui.column().classes('p-3 gap-1'):
                ui.label('🤖 Assistant').classes('font-medium !text-base')
                ui.label('New conversation. How can I help you?').classes(
                    '!text-base !leading-relaxed text-gray-700'
                )


def create_chat_window() -> Any:
    """
    Create a chat window container with helper to append messages.
    Returns the container element with methods:
      - append_message(role: str, text: str)
    Uses NiceGUI's native clear() for proper container clearing when switching modes.
    Shows a friendly welcome message when the chat first opens.
    """
    container = ui.column().classes('flex-1 overflow-auto p-4 space-y-4 w-full bg-white rounded-lg shadow-sm border')

    render_welcome_message(container)

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

