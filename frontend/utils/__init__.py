"""Utility functions for RescueBox Desktop"""

from frontend.utils.file_browser import browse_directory, browse_file
from frontend.utils.validators import validate_form_data, validate_input, validate_parameter
from frontend.utils.path_setup import setup_backend_path
from frontend.utils.error_handling import (
    handle_api_error,
    show_error_to_user,
    show_success_to_user,
    handle_validation_error
)

# NiceGUI storage utilities (conditional import to avoid dependency if not available)
try:
    from frontend.utils.user_preferences import (
        get_user_preferences,
        set_user_preference,
        set_user_preferences,
        get_user_preference,
        reset_user_preferences
    )
    from frontend.utils.nicegui_storage import (
        get_user_id,
        get_current_conversation_id,
        set_current_conversation_id,
        get_draft_message,
        set_draft_message,
        get_form_draft,
        set_form_draft
    )
    _NICEGUI_STORAGE_AVAILABLE = True
except ImportError:
    # NiceGUI storage utilities not available (e.g., during testing without NiceGUI context)
    _NICEGUI_STORAGE_AVAILABLE = False

__all__ = [
    'browse_directory',
    'browse_file',
    'validate_form_data',
    'validate_input',
    'validate_parameter',
    'setup_backend_path',
    'handle_api_error',
    'show_error_to_user',
    'show_success_to_user',
    'handle_validation_error',
]

# Conditionally export NiceGUI storage utilities
if _NICEGUI_STORAGE_AVAILABLE:
    __all__.extend([
        'get_user_preferences',
        'set_user_preference',
        'set_user_preferences',
        'get_user_preference',
        'reset_user_preferences',
        'get_user_id',
        'get_current_conversation_id',
        'set_current_conversation_id',
        'get_draft_message',
        'set_draft_message',
        'get_form_draft',
        'set_form_draft',
    ])
