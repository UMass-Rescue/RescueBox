"""
Application Constants

This module provides centralized constants for UI strings, status messages,
and other application-wide constants. This makes it easier to maintain
consistent terminology and enables future internationalization.

Usage:
    from frontend.constants import UI_TITLES, STATUS_MESSAGES
    
    ui.label(UI_TITLES['models'])
    status_text.value = STATUS_MESSAGES['ready']
"""

# UI Titles
UI_TITLES = {
    'models': 'Available Plugins',
    'jobs': 'Jobs',
    'chatbot': 'RescueBox Assistant',
    'logs': 'Application Logs',
    'model_details': 'Plugin Details',
    'job_details': 'Job Details',
    'home': 'Welcome to RescueBox',
    'home_subtitle': 'Browse rescuebox plugin details or Use the Assistant to get started',
}

# Home page: inline User ID (required before using jobs / persistent chat)
HOME_USER_ID = {
    'title': 'Set your User ID',
    'blurb': (
        'Enter a new or existing ID to link your jobs and chat history. '
        'Use the same ID each time you open RescueBox.'
    ),
    'input_label': 'User ID',
    'placeholder': 'e.g. your name or case number',
    'save_button': 'Save and continue',
    'current_prefix': 'User ID:',
    'change_user_button': 'Change User ID',
    'change_user_hint': 'Use this if you need to sign in with a different ID. Empty job history is normal for a new ID.',
}

# UI Button Labels
UI_BUTTONS = {
    'refresh': 'Refresh',
    'submit': 'Submit Job',
    'cancel': 'Cancel',
    'delete': 'Delete',
    'view': 'View',
    'inspect': 'Inspect',
    'plugin_readme': 'README',  # Browse Plugins model card → plugin details / app-info
    'run': 'Run Model',
    'connect': 'Connect',
    'browse_models': 'Browse Plugins',
    'open_assistant': 'Open Assistant',
    'view_jobs': 'View Jobs',
    'new_conversation': 'New Conversation',
    'attach_files': 'Attach Files',
    'model_doc': 'Model Doc',
    'resubmit': 'Re-submit Job',
}

# Status Messages
STATUS_MESSAGES = {
    'ready': 'Ready',
    'thinking': 'Thinking...',
    'loading': 'Loading...',
    'processing': 'Processing...',
    'error': 'An error occurred',
    'success': 'Success',
    'online': 'Online',
    'offline': 'Offline',
}

# Job Status Labels
JOB_STATUS = {
    'running': 'Running',
    'completed': 'Completed',
    'failed': 'Failed',
    'canceled': 'Canceled',
}

# Navigation Links
NAV_LINKS = {
    'models': '/models',
    'jobs': '/jobs',
    'chatbot': '/chatbot',
    'logs': '/logs',
    'demo': '/demo',
    'home': '/',
}

# Error Messages
ERROR_MESSAGES = {
    'generic': 'An error occurred. Please try again.',
    'api_error': 'Failed to communicate with server. Please check your connection.',
    'not_found': 'The requested resource was not found.',
    'validation_error': 'Please check the form for errors.',
    'load_models': 'Unable to load models. Please try again.',
    'load_jobs': 'Unable to load jobs. Please try again.',
    'submit_job': 'Failed to submit job. Please try again.',
    'delete_job': 'Failed to delete job.',
    'cancel_job': 'Failed to cancel job.',
}

# Success Messages
SUCCESS_MESSAGES = {
    'job_submitted': 'Job submitted successfully',
    'job_deleted': 'Job deleted',
    'job_canceled': 'Job canceled',
    'models_loaded': 'Models loaded successfully',
}

# Model Configuration
# fine tuned

# default https://huggingface.co/ibm-granite/granite-4.0-micro-GGUF/blob/main/granite-4.0-micro-Q4_0.gguf

DEFAULT_GRANITE_GGUF_MODEL_PATH = r"./granite-4.0-micro-Q4_0.gguf"
# DEFAULT_GRANITE_GGUF_MODEL_PATH = r"./granite-4.0-micro-f16.gguf"
