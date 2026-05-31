"""Pages package — importing submodules registers NiceGUI ``@ui.page`` routes."""

from frontend.pages.models import models_page, ModelsPage
from frontend.pages.jobs import jobs_page, job_details_page, JobsPage
from frontend.pages.chatbot import chatbot_page, ChatbotPage
from frontend.pages.logs import logs_page, LogsPage
from frontend.pages.page_utils import get_page_title, setup_common_imports, create_page_metadata, log_page_action

# Additional routes not re-exported below (import for @ui.page registration only)
from frontend.pages import about as _about_page  # noqa: F401
from frontend.pages import demo as _demo_page  # noqa: F401
from frontend.pages import demo_quick_start as _demo_quick_start  # noqa: F401
from frontend.pages import demo_transcribe_walkthrough as _demo_transcribe  # noqa: F401
from frontend.pages import demo_image_summary_walkthrough as _demo_image  # noqa: F401
from frontend.pages import demo_other_walkthrough as _demo_other  # noqa: F401
from frontend.pages import licenses_copyright as _licenses_page  # noqa: F401

__all__ = [
    'models_page', 'ModelsPage',
    'jobs_page', 'job_details_page', 'JobsPage',
    'chatbot_page', 'ChatbotPage',
    'logs_page', 'LogsPage',
    'get_page_title', 'setup_common_imports', 'create_page_metadata', 'log_page_action',
]
