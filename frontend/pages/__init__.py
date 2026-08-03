"""Pages package — importing submodules registers NiceGUI ``@ui.page`` routes."""

# Import submodules so @ui.page handlers register (referenced to satisfy F401).
from frontend.pages import (
    about,
    demo,
    demo_image_summary_walkthrough,
    demo_other_walkthrough,
    demo_quick_start,
    demo_transcribe_walkthrough,
    home,
    licenses_copyright,
)
from frontend.pages.chatbot import ChatbotPage, chatbot_page
from frontend.pages.jobs import JobsPage, job_details_page, jobs_page
from frontend.pages.logs import LogsPage, logs_page
from frontend.pages.models import ModelsPage, models_page
from frontend.pages.page_utils import (
    create_page_metadata,
    get_page_title,
    log_page_action,
)

__all__ = [
    "ChatbotPage",
    "JobsPage",
    "LogsPage",
    "ModelsPage",
    "about",
    "chatbot_page",
    "create_page_metadata",
    "demo",
    "demo_image_summary_walkthrough",
    "demo_other_walkthrough",
    "demo_quick_start",
    "demo_transcribe_walkthrough",
    "get_page_title",
    "home",
    "job_details_page",
    "jobs_page",
    "licenses_copyright",
    "log_page_action",
    "logs_page",
    "models_page",
]
