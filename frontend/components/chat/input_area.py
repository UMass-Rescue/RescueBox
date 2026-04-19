from typing import Optional, Callable
from nicegui import ui

from frontend.design_tokens import Design


def create_input_area(status_text_ref: Optional[object], on_send: Callable):
    """
    Create the chatbot input area as a reusable component.

    Returns the container element that holds the input area.
    """
    # rb-chat-input-area: global CSS in ui_readability_css.py bumps label/textarea/button/status
    input_area = ui.column().classes(
        "rb-chat-input-area w-full max-w-none flex-none bg-white border-t border-zinc-100 "
        "p-4"
    )

    with input_area:
        # Composer-only wrapper: ``set_input_enabled(False)`` hides this block so re-run
        # forms (siblings appended below in the same ``input_area``) stay visible.
        with ui.column().classes("rb-chat-composer-core w-full") as composer_strip:
            # Put the textarea on its own full-width row so it can expand comfortably.
            with ui.row().classes("w-full"):
                input_field = ui.textarea(
                    label="Type your request",
                    placeholder="Type in a rescuebox task...or /help",
                ).classes(Design.INPUT_MODERN).props("rows=4")

            # Controls row: send button and status; kept compact below the textarea.
            with ui.row().classes("w-full items-center gap-3 mt-2"):
                send_button = ui.button("Send", icon="send", on_click=on_send).classes(
                    f"{Design.BTN_PRIMARY} !text-base min-h-0"
                )

                # Status and spinner
                with ui.row().classes("items-center gap-2 px-2"):
                    status_spinner = ui.spinner(size="1.25rem").classes(
                        Design.SPINNER_PROCESSING
                    )
                    status_label = ui.label().classes("!text-base text-zinc-600")
                    if status_text_ref:
                        status_spinner.bind_visibility_from(status_text_ref, 'is_processing')
                        status_label.bind_text_from(status_text_ref, 'status_text')

    # Attach references for callers that expect them (e.g., ChatUIBuilder)
    input_area.composer_strip = composer_strip
    input_area.input_field = input_field
    input_area.send_button = send_button
    input_area.status_label = status_label
    input_area.status_spinner = status_spinner
    # Expose the most recently created input_area for other modules that need to
    # render forms into the input area (fallback for rerun flows).
    try:
        # module-level variable
        globals()['_LAST_INPUT_AREA'] = input_area
    except Exception:
        pass

    return input_area


def get_latest_input_area():
    """Return the most recently created input_area element, or None."""
    return globals().get('_LAST_INPUT_AREA')

