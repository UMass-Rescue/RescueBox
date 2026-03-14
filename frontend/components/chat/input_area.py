from typing import Optional, Callable
from nicegui import ui


def create_input_area(status_text_ref: Optional[object], on_send: Callable):
    """
    Create the chatbot input area as a reusable component.

    Returns the container element that holds the input area.
    """
    # Make the input area take the full available width; remove horizontal margins
    # so the textarea can expand to the browser width when the page layout allows it.
    input_area = ui.column().classes('w-full max-w-none bg-white border-t shadow-lg p-2 mb-2 rounded-t-lg')

    with input_area:
        # Put the textarea on its own full-width row so it can expand comfortably.
        with ui.row().classes('w-full'):
            input_field = ui.textarea(
                label='Type your request',
                placeholder='Type in a rescuebox task...or /help'
            ).classes('w-full min-w-0 p-3').props('rows=4')

        # Controls row: send button and status; kept compact below the textarea.
        with ui.row().classes('w-full items-center gap-3 mt-2'):
            send_button = ui.button('Send', on_click=on_send).classes('bg-blue-600 text-white px-4 py-2')

            # Status and spinner
            with ui.row().classes('items-center gap-2 px-2'):
                status_spinner = ui.spinner(size='sm').classes('text-blue-600')
                status_label = ui.label().classes('text-sm text-gray-600')
                if status_text_ref:
                    status_spinner.bind_visibility_from(status_text_ref, 'is_processing')
                    status_label.bind_text_from(status_text_ref, 'status_text')

    # Attach references for callers that expect them (e.g., ChatUIBuilder)
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

