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

__all__ = [
    "ChatbotPage",
    "JobsPage",
    "LogsPage",
    "ModelsPage",
    "about",
    "chatbot_page",
    "demo",
    "demo_image_summary_walkthrough",
    "demo_other_walkthrough",
    "demo_quick_start",
    "demo_transcribe_walkthrough",
    "home",
    "job_details_page",
    "jobs_page",
    "licenses_copyright",
    "logs_page",
    "models_page",
]
