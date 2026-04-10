"""Application Constants

This module provides centralized constants for UI strings, status messages,
and other application-wide constants. This makes it easier to maintain
consistent terminology and enables future internationalization.

Usage:
    from frontend.constants import UI_TITLES, STATUS_MESSAGES
    
    ui.label(UI_TITLES['models'])
    status_text.value = STATUS_MESSAGES['ready']
"""

from typing import Optional

# Demo User ID: fixed prefix + exactly two characters (password-style gate for the UI)
DEMO_USER_ID_PREFIX = "rb_demo_0408_"
DEMO_USER_ID_SUFFIX_LEN = 2


def is_valid_explicit_user_id(value: Optional[str]) -> bool:
    """
    True if value is exactly DEMO_USER_ID_PREFIX followed by DEMO_USER_ID_SUFFIX_LEN characters.
    """
    if not value or not isinstance(value, str):
        return False
    s = value.strip()
    p = DEMO_USER_ID_PREFIX
    if len(s) != len(p) + DEMO_USER_ID_SUFFIX_LEN:
        return False
    return s.startswith(p)


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
        'Enter the demo User ID '
        'Use the same value each time you open RescueBox.'
    ),
    'input_label': 'User ID',
    'placeholder': '??',
    'save_button': 'Save and continue',
    'current_prefix': 'User ID:',
    'change_user_button': 'Change User ID',
    'change_user_hint': 'Use this if you need to sign in with a different ID.',
    'invalid_format': (
        'User ID is not correct.'
    ),
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

# Deep link to the "Sample inputs & outputs" section on the Demo page (HTML id: sample-inputs), all folders
DEMO_SAMPLE_INPUTS_URL = f"{NAV_LINKS['demo']}#sample-inputs"


def demo_samples_url(walkthrough: Optional[str] = None) -> str:
    """
    Link to /demo sample explorer with the same folder filter as ``render_walkthrough_samples_panel``.

    ``walkthrough`` must be one of: transcribe, image_search, other, quick_start, all.
    Use ``all`` or omit for the full tree (equivalent to :data:`DEMO_SAMPLE_INPUTS_URL` without query).

    Example: ``/demo?walkthrough=transcribe#sample-inputs``

    Note: ``#walkthrough-samples`` is only for walkthrough *routes*; on /demo use ``#sample-inputs``.
    """
    base = NAV_LINKS['demo']
    fragment = '#sample-inputs'
    if not walkthrough:
        return f'{base}{fragment}'
    w = str(walkthrough).strip().lower().replace('-', '_')
    allowed = frozenset({'transcribe', 'image_search', 'other', 'quick_start', 'all'})
    if w not in allowed or w == 'all':
        return f'{base}{fragment}'
    return f'{base}?walkthrough={w}{fragment}'

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
