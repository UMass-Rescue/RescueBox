import logging
import asyncio
from nicegui import ui
from frontend.design_tokens import Design

# Legacy name kept for imports / __all__; prefer Design in new code.
UIStyling = Design

logger = logging.getLogger(__name__)

_LATEST_INPUT_AREA = None

def set_latest_input_area(container):
    global _LATEST_INPUT_AREA
    _LATEST_INPUT_AREA = container

def get_latest_input_area():
    return _LATEST_INPUT_AREA

class UIOperations:
    @staticmethod
    def safe_notify(message: str, type: str = "info"):
        from frontend.utils import notify_info, notify_success, notify_error, notify_warning
        if type == "success": notify_success(message)
        elif type == "error": notify_error(message)
        elif type == "warning": notify_warning(message)
        else: notify_info(message)

    @staticmethod
    def scroll_to_bottom(client=None):
        try: (client or ui).run_javascript("window.scrollTo(0, document.body.scrollHeight)")
        except: pass

    @staticmethod
    def scroll_document_to_bottom(client=None):
        try: (client or ui).run_javascript("window.scrollTo(0, document.body.scrollHeight)")
        except: pass

    @staticmethod
    def scroll_form_into_view():
        # Minimal implementation for now
        pass

    @staticmethod
    async def safe_container_update(container):
        try:
            if hasattr(container, 'update'): container.update()
            await asyncio.sleep(0.01)
        except: pass

    @staticmethod
    async def scroll_to_bottom_after_dom_update(client=None):
        await asyncio.sleep(0.05)
        UIOperations.scroll_to_bottom(client)

    @staticmethod
    def scroll_form_into_view_with_retries(client=None):
        # Implementation if needed
        pass
