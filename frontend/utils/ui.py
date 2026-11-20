import inspect
import logging
from typing import Any, Callable, Coroutine, TypeVar, overload

from nicegui import context, ui

from frontend.config import APP_DARK_MODE
from frontend.constants import HOME_USER_ID, NAV_LINKS
from frontend.utils.exceptions import UI_RENDER_ERRORS
from frontend.utils.storage import (
    ensure_explicit_user_id_for_tests,
    get_user_id,
    get_user_id_for_jobs,
    get_user_preference,
)

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


def is_ephemeral_ui_error(exc: BaseException) -> bool:
    """True when the client disconnected or NiceGUI has no slot (tests/background)."""
    msg = str(exc).lower()
    return (
        "client deleted" in msg
        or "client is deleted" in msg
        or "slot cannot be determined" in msg
        or "no slot to add element" in msg
    )


@overload
def safe_ui_call(
    func: Callable[..., Coroutine[Any, Any, _T]],
    *args: Any,
    check_slot: bool = False,
    **kwargs: Any,
) -> Coroutine[Any, Any, _T | None]: ...


@overload
def safe_ui_call(
    func: Callable[..., _T],
    *args: Any,
    check_slot: bool = False,
    **kwargs: Any,
) -> _T | None: ...


def safe_ui_call(
    func: Callable[..., Any],
    *args: Any,
    check_slot: bool = False,
    **kwargs: Any,
) -> Any:
    """Safely call a UI function, swallowing ephemeral UI errors or slot unavailability.

    Args:
        func: The UI function or coroutine function to call.
        *args: Positional arguments for the function.
        check_slot: If True, checks that a NiceGUI slot is available before executing
            non-mock callables.
        **kwargs: Keyword arguments for the function.
    """
    if check_slot and not (hasattr(func, "called") or hasattr(func, "mock_calls")):
        try:
            if not context.slot_stack:
                return None
        except Exception:
            pass

    def handle_error(e: BaseException):
        if is_ephemeral_ui_error(e):
            return None
        raise e

    if inspect.iscoroutinefunction(func):

        async def async_wrapper():
            try:
                return await func(*args, **kwargs)
            except UI_RENDER_ERRORS as e:
                return handle_error(e)

        return async_wrapper()

    try:
        return func(*args, **kwargs)
    except UI_RENDER_ERRORS as e:
        return handle_error(e)


# Backward compatibility alias
_safe_ui_call = safe_ui_call


def notify_success(
    message: str,
    duration: float = 3.0,
    position: str = "top",
    close_button: bool = True,
    **kwargs: Any,
) -> None:
    logger.debug("Success notification shown: %s", message)
    safe_ui_call(
        ui.notify,
        message,
        type="positive",
        timeout=int(duration * 1000),
        position=position,
        close_button=close_button,
        check_slot=True,
        **kwargs,
    )


def notify_error(
    message: str,
    duration: float = 5.0,
    position: str = "top",
    close_button: bool = True,
    **kwargs: Any,
) -> None:
    logger.debug("Error notification shown: %s", message)
    safe_ui_call(
        ui.notify,
        message,
        type="negative",
        timeout=int(duration * 1000),
        position=position,
        close_button=close_button,
        check_slot=True,
        **kwargs,
    )


def notify_info(
    message: str,
    duration: float = 3.0,
    position: str = "top",
    close_button: bool = True,
    **kwargs: Any,
) -> None:
    logger.debug("Info notification shown: %s", message)
    safe_ui_call(
        ui.notify,
        message=message,
        timeout=int(duration * 1000),
        position=position,
        close_button=close_button,
        check_slot=True,
        **kwargs,
    )


def notify_warning(
    message: str,
    duration: float = 4.0,
    position: str = "top",
    close_button: bool = True,
    **kwargs: Any,
) -> None:
    logger.debug("Warning notification shown: %s", message)
    safe_ui_call(
        ui.notify,
        message,
        type="warning",
        timeout=int(duration * 1000),
        position=position,
        close_button=close_button,
        check_slot=True,
        **kwargs,
    )


async def handle_api_error(
    error: Exception, context_str: str, show_to_user: bool = True
):
    logger.error("%s: %s", context_str, error, exc_info=True)
    if show_to_user:
        notify_error(f"Error: {error}")


def show_error_to_user(message: str):
    notify_error(message)


def show_success_to_user(message: str):
    notify_success(message)


def handle_validation_error(
    errors: dict | list, context_str: str = "Form validation failed"
):
    logger.warning("%s: %s", context_str, errors)
    if isinstance(errors, dict) and errors:
        notify_warning(str(next(iter(errors.values()))))
        return
    notify_warning("Form validation failed. Please check your inputs.")


def ensure_session_user_id():
    """Ensure a NiceGUI session user id exists (browser session identity)."""
    return get_user_id()


def ensure_active_case_id():
    """Return the active investigative case id (required for jobs and scoped history)."""
    return get_user_id_for_jobs()


def ensure_user_id():
    """Alias for :func:`ensure_session_user_id` (session id, not active case)."""
    return ensure_session_user_id()


def apply_saved_theme():
    """Apply dark/light mode from user preferences or ``RESCUEBOX_DARK_MODE``."""
    pref = get_user_preference("dark_mode")
    use_dark = APP_DARK_MODE if pref is None else bool(pref)
    try:
        ui.dark_mode(use_dark)
    except UI_RENDER_ERRORS:
        logger.debug("Could not apply theme (no client context)")


def require_demo_user_session():
    ensure_explicit_user_id_for_tests()
    if get_user_id_for_jobs():
        return True

    with ui.column().classes(
        "container mx-auto px-4 sm:px-8 py-8 max-w-2xl w-full pb-16"
    ):
        ui.label(HOME_USER_ID["title"]).classes("text-2xl font-semibold mb-2")
        ui.label(HOME_USER_ID["blurb"]).classes("text-zinc-600 mb-4")
        ui.link("Go to Home", NAV_LINKS["home"]).classes(
            "text-[#a2aaad] hover:text-[#8a9194] hover:underline"
        )
    return False


def select(*args, **kwargs):
    """Alias for ui.select with default behavior or styling."""
    return ui.select(*args, **kwargs)
