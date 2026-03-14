"""
UI Styling.

Centralized UI styling constants and utilities.
"""


class UIStyling:
    """Centralized UI styling constants and utilities."""

    # Card styles
    CARD_TOOL_CALL = 'p-4 my-2 bg-blue-50 border-blue-200'
    CARD_TOOL_RESULT = 'p-4 my-2 bg-green-50 border-green-200'
    CARD_ERROR = 'p-4 my-2 bg-red-50 border-red-200'

    # Label styles
    LABEL_TOOL_CALL_TITLE = 'font-semibold text-blue-800'
    LABEL_TOOL_CALL_ARGS = 'text-sm text-blue-600 mt-1'
    LABEL_TOOL_RESULT_TITLE = 'font-semibold text-green-800 mt-3'
    LABEL_TOOL_RESULT_CONTENT = 'text-sm text-green-700 mt-1 whitespace-pre-wrap'
    LABEL_ERROR_TITLE = 'font-semibold text-red-800'
    LABEL_ERROR_CONTENT = 'text-sm text-red-700 mt-1'

    # Button styles
    BUTTON_RERUN_TOOL = 'mt-2 bg-blue-600 text-white px-3 py-1 rounded text-sm'

    # Error display styles
    CARD_ERROR_DISPLAY = 'bg-red-50 border-2 border-red-300 rounded-lg p-6 m-4 shadow-lg'
    ICON_ERROR = 'text-red-600 mt-1'
    LABEL_ERROR_DISPLAY_TITLE = 'text-xl font-bold text-red-800 mb-2'
    LABEL_ERROR_DISPLAY_MESSAGE = 'text-red-700 mb-3 leading-relaxed'
    EXPANSION_ERROR_DETAILS = 'bg-red-100 border border-red-200 rounded'
    LABEL_ERROR_TECHNICAL = 'text-sm text-red-600 font-mono p-2 whitespace-pre-wrap'
    LABEL_INLINE_ERROR = 'text-red-600 p-4 bg-red-50 rounded-lg border-2 border-red-300'

    # Status and spinner styles
    SPINNER_PROCESSING = 'text-green-600'
    LABEL_PROCESSING = 'ml-2 text-green-700'

    # Button states
    BUTTON_DISABLED = 'bg-gray-400 text-gray-300 cursor-not-allowed'
    BUTTON_ENABLED = 'bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-medium transition-colors'

    # Input styles
    INPUT_ENABLED = 'flex-1 min-w-96 rounded-xl border-2 border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 transition-all duration-200 resize-none shadow-sm'
    INPUT_DISABLED = 'flex-1 min-w-96 rounded-xl border-2 border-gray-200 bg-gray-100 text-gray-500 cursor-not-allowed resize-none shadow-sm'

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
            'processing': 'text-blue-600',
            'success': 'text-green-600',
            'error': 'text-red-600',
            'ready': 'text-gray-600'
        }
        return colors.get(status, 'text-gray-600')
