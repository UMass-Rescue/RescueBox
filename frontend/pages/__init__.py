"""Pages package — importing submodules registers NiceGUI ``@ui.page`` routes."""

from frontend.pages.models import models_page, ModelsPage
from frontend.pages.jobs import jobs_page, job_details_page, JobsPage
from frontend.pages.chatbot import chatbot_page, ChatbotPage
from frontend.pages.logs import logs_page, LogsPage
from frontend.pages.page_utils import (
    get_page_title,
    setup_common_imports,
    create_page_metadata,
    log_page_action,
)

# Import submodules so @ui.page handlers register (referenced to satisfy F401).
from frontend.pages import (
    about,
    demo,
    demo_image_summary_walkthrough,
    demo_other_walkthrough,
    demo_quick_start,
    demo_transcribe_walkthrough,
    licenses_copyright,
)

__all__ = [
    "models_page",
    "ModelsPage",
    "jobs_page",
    "job_details_page",
    "JobsPage",
    "chatbot_page",
    "ChatbotPage",
    "logs_page",
    "LogsPage",
    "get_page_title",
    "setup_common_imports",
    "create_page_metadata",
    "log_page_action",
    "about",
    "demo",
    "demo_quick_start",
    "demo_transcribe_walkthrough",
    "demo_image_summary_walkthrough",
    "demo_other_walkthrough",
    "licenses_copyright",
]
