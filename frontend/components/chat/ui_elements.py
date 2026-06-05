from typing import Callable, Any, Optional
from nicegui import ui
from frontend.design_tokens import Design
from .rendering import render_welcome_message
from .utils import set_latest_input_area


def create_chat_header(on_show_history: Optional[Callable] = None):
    with ui.row().classes(
        "rb-chat-toolbar-floating items-center justify-end w-full px-4 py-3 sticky top-0 z-10 gap-3"
    ):
        models_btn = (
            ui.button("Menu", icon="menu", color=None)
            .classes(Design.BTN_PRIMARY_COMPACT)
            .props("unelevated no-caps")
        )
        analyze_btn = (
            ui.button("Chat", icon="chat", color=None)
            .classes(Design.BTN_PRIMARY_COMPACT)
            .props("unelevated no-caps")
        )
        history_btn = (
            ui.button("History", icon="history", color=None, on_click=on_show_history)
            .classes(Design.BTN_PRIMARY_COMPACT)
            .props("unelevated no-caps")
        )
    return models_btn, analyze_btn, history_btn


def create_chat_window() -> Any:
    # Use flex-1 to ensure it expands to available space in the card
    container = ui.column().classes(
        "rb-chat-messages-scroll w-full flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50 min-w-0"
    )
    render_welcome_message(container)
    return container


def create_input_area(status_text_ref: Optional[object], on_send: Callable):
    input_area = ui.column().classes(
        "rb-chat-input-area w-full flex-none bg-white border-t border-slate-200 p-4"
    )
    set_latest_input_area(input_area)
    with input_area:
        with ui.column().classes("rb-chat-composer-core w-full") as composer_strip:
            input_field = (
                ui.textarea(label="Type your request")
                .classes(Design.INPUT_MODERN)
                .props("rows=4")
            )
            with ui.row().classes("w-full items-center gap-3 mt-2"):
                send_button = ui.button("Send", icon="send", on_click=on_send).classes(
                    f"{Design.BTN_PRIMARY} !text-base"
                )
                status_label = ui.label().classes("!text-base text-zinc-600")
                if status_text_ref:
                    status_label.bind_text_from(status_text_ref, "status_text")
                    # Add a spinner that only shows while processing
                # Use explicit UMass Maroon hex for spinner to avoid indigo defaults
                spinner = ui.spinner(color="#881c1c", size="sm").classes("ml-1")
                status_text_ref.attach_processing_strip(spinner)

    input_area.input_field = input_field
    input_area.send_button = send_button
    input_area.status_label = status_label
    input_area.composer_strip = composer_strip
    return input_area
