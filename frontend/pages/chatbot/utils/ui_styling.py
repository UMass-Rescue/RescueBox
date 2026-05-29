"""
UI Styling.

Centralized UI styling constants and utilities (uses :mod:`frontend.design_tokens`).
"""

from frontend.design_tokens import Design


class UIStyling:
    """Centralized UI styling constants and utilities."""

    # Card styles
    CARD_TOOL_CALL = Design.CARD_TOOL_CALL
    CARD_TOOL_RESULT = Design.CARD_TOOL_RESULT
    CARD_ERROR = "p-4 my-2 bg-red-50 border border-red-200 rounded-lg"

    # Label styles
    LABEL_TOOL_CALL_TITLE = Design.LABEL_TOOL_CALL_TITLE
    LABEL_TOOL_CALL_ARGS = Design.LABEL_TOOL_CALL_ARGS
    LABEL_TOOL_RESULT_TITLE = Design.LABEL_TOOL_RESULT_TITLE
    LABEL_TOOL_RESULT_CONTENT = Design.LABEL_TOOL_RESULT_CONTENT
    LABEL_ERROR_TITLE = "font-semibold text-red-800"
    LABEL_ERROR_CONTENT = "text-sm text-red-700 mt-1"

    # Button styles
    BUTTON_RERUN_TOOL = f"mt-2 {Design.BTN_PRIMARY_TIGHT}"

    # Error display styles
    CARD_ERROR_DISPLAY = "bg-red-50 border-2 border-red-300 rounded-lg p-6 m-4 shadow-lg"
    ICON_ERROR = "text-red-600 mt-1"
    LABEL_ERROR_DISPLAY_TITLE = "text-xl font-bold text-red-800 mb-2"
    LABEL_ERROR_DISPLAY_MESSAGE = "text-red-700 mb-3 leading-relaxed"
    EXPANSION_ERROR_DETAILS = "bg-red-100 border border-red-200 rounded"
    LABEL_ERROR_TECHNICAL = "text-sm text-red-600 font-mono p-2 whitespace-pre-wrap"
    LABEL_INLINE_ERROR = "text-red-600 p-4 bg-red-50 rounded-lg border-2 border-red-300"

    # Status and spinner styles
    SPINNER_PROCESSING = Design.SPINNER_PROCESSING
    LABEL_PROCESSING = "ml-2 text-green-700"

    # Button states (composer send / forms — true disabled gray)
    BUTTON_DISABLED = Design.BTN_DISABLED
    BUTTON_ENABLED = Design.BTN_PRIMARY

    # Chat toolbar (Menu / Chat / History): solid maroon at all times (mode is shown on the card badge).
    CHAT_HEADER_BUTTON = (
        f"{Design.BTN_PRIMARY_COMPACT} !text-base sm:!text-lg min-h-0 shadow-sm"
    )

    # Input styles (chat composer / long text)
    INPUT_ENABLED = (
        f"flex-1 min-w-96 {Design.INPUT_OUTLINED} bg-white text-zinc-900 placeholder-zinc-400"
    )
    INPUT_DISABLED = (
        "flex-1 min-w-96 rounded-xl border-2 border-zinc-200 bg-zinc-100 text-zinc-500 "
        "cursor-not-allowed resize-none shadow-sm"
    )

    @staticmethod
    def get_button_classes(enabled: bool = True) -> str:
        """Get button classes based on enabled state."""
        return UIStyling.BUTTON_ENABLED if enabled else UIStyling.BUTTON_DISABLED

    @staticmethod
    def get_input_classes(enabled: bool = True) -> str:
        """Get input classes based on enabled state."""
        return UIStyling.INPUT_ENABLED if enabled else UIStyling.INPUT_DISABLED

    @staticmethod
    def get_send_button_classes(enabled: bool = True) -> str:
        """Get send button classes based on enabled state."""
        return UIStyling.BUTTON_ENABLED if enabled else UIStyling.BUTTON_DISABLED

    @staticmethod
    def get_status_color(status: str) -> str:
        """Get color class for status."""
        colors = {
            "processing": Design.STATUS_PROCESSING,
            "success": "text-green-600",
            "error": "text-red-600",
            "ready": "text-zinc-600",
        }
        return colors.get(status, "text-zinc-600")
