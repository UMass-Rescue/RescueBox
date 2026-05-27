"""Pages package"""

from frontend.pages.models import models_page, ModelsPage
from frontend.pages.jobs import jobs_page, job_details_page, JobsPage
from frontend.pages.chatbot import chatbot_page, ChatbotPage
from frontend.pages.logs import logs_page, LogsPage
from frontend.pages.page_utils import get_page_title, setup_common_imports, create_page_metadata, log_page_action

__all__ = [
    'models_page', 'ModelsPage',
    'jobs_page', 'job_details_page', 'JobsPage',
    'chatbot_page', 'ChatbotPage',
    'logs_page', 'LogsPage',
    'get_page_title', 'setup_common_imports', 'create_page_metadata', 'log_page_action',
]
