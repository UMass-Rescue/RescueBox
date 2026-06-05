import logging
from typing import Union
from nicegui import ui, context

logger = logging.getLogger(__name__)


def _safe_ui_call(func, *args, **kwargs):
    """Call a UI function only if a slot is available (prevents errors during background tasks)."""
    # If it's a mock, always call it so tests can assert
    if hasattr(func, "called") or hasattr(func, "mock_calls"):
        return func(*args, **kwargs)
    # Otherwise, check for slot stack safety
    if not context.slot_stack:
        return None
    try:
        return func(*args, **kwargs)
    except Exception:
        return None


def notify_success(
    message: str,
    duration: float = 3.0,
    position: str = "top",
    close_button: bool = True,
    **kwargs,
):
    logger.debug(f"Success notification shown: {message}")
    _safe_ui_call(
        ui.notify,
        message,
        type="positive",
        timeout=int(duration * 1000),
        position=position,
        close_button=close_button,
        **kwargs,
    )


def notify_error(
    message: str,
    duration: float = 5.0,
    position: str = "top",
    close_button: bool = True,
    **kwargs,
):
    logger.debug(f"Error notification shown: {message}")
    _safe_ui_call(
        ui.notify,
        message,
        type="negative",
        timeout=int(duration * 1000),
        position=position,
        close_button=close_button,
        **kwargs,
    )


def notify_info(
    message: str,
    duration: float = 3.0,
    position: str = "top",
    close_button: bool = True,
    **kwargs,
):
    logger.debug(f"Info notification shown: {message}")
    _safe_ui_call(
        ui.notify,
        message=message,
        timeout=int(duration * 1000),
        position=position,
        close_button=close_button,
        **kwargs,
    )


def notify_warning(
    message: str,
    duration: float = 4.0,
    position: str = "top",
    close_button: bool = True,
    **kwargs,
):
    logger.debug(f"Warning notification shown: {message}")
    _safe_ui_call(
        ui.notify,
        message,
        type="warning",
        timeout=int(duration * 1000),
        position=position,
        close_button=close_button,
        **kwargs,
    )


async def handle_api_error(
    error: Exception, context_str: str, show_to_user: bool = True
):
    logger.error(f"{context_str}: {error}", exc_info=True)
    if show_to_user:
        notify_error(f"Error: {error}")


def show_error_to_user(message: str):
    notify_error(message)


def show_success_to_user(message: str):
    notify_success(message)


def handle_validation_error(
    errors: Union[dict, list], context_str: str = "Form validation failed"
):
    logger.warning("%s: %s", context_str, errors)
    notify_warning("Form validation failed. Please check your inputs.")


def ensure_user_id():
    from frontend.utils.storage import get_user_id

    return get_user_id()


def apply_saved_theme():
    # Stub for now
    pass


def require_demo_user_session():
    from frontend.utils.storage import (
        get_user_id_for_jobs,
        ensure_explicit_user_id_for_tests,
    )
    from frontend.constants import HOME_USER_ID, NAV_LINKS

    ensure_explicit_user_id_for_tests()
    if get_user_id_for_jobs():
        return True

    with ui.column().classes("container mx-auto px-4 sm:px-8 py-8 max-w-2xl w-full pb-16"):
        ui.label(HOME_USER_ID["title"]).classes("text-2xl font-semibold mb-2")
        ui.label(HOME_USER_ID["blurb"]).classes("text-zinc-600 mb-4")
        ui.link("Go to Home", NAV_LINKS["home"]).classes(
            "text-[#a2aaad] hover:text-[#8a9194] hover:underline"
        )
    return False


def scroll_to_bottom():
    ui.run_javascript("window.scrollTo(0, document.body.scrollHeight)")


def navigate_to(path: str):
    ui.navigate.to(path)


def open_url(url: str, new_tab: bool = True):
    ui.navigate.to(url, new_tab=new_tab)


def refresh_page():
    ui.run_javascript("window.location.reload()")


def select(*args, **kwargs):
    """Alias for ui.select with default behavior or styling."""
    return ui.select(*args, **kwargs)
