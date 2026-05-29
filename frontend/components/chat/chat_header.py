import logging
from nicegui import ui
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def user_has_job_history() -> bool:
    """True when the current user has at least one job row (any status)."""
    try:
        from frontend.database import get_job_db
        from frontend.utils.nicegui_storage import get_user_id_for_jobs

        uid = get_user_id_for_jobs()
        if not uid:
            return False
        return get_job_db().get_job_count_for_user(uid) > 0
    except Exception:
        return False


def create_chat_header(on_new_conversation: Callable, ui_state: dict, ui_styling: Any = None, on_show_history: Callable = None):
    """
    Create the chat header row used by ChatUIBuilder.

    Returns (models_btn, analyze_btn, history_btn). Title and mode badge are on the main chat card.
    """
    mode_indicator = None
    models_btn = None
    analyze_btn = None

    # Toolbar only: title + mode badge live on the main chat card (see ChatUIBuilder).
    from frontend.pages.chatbot.utils.ui_styling import UIStyling

    # No bar behind buttons — page background shows through; maroon carries the chrome.
    with ui.row().classes(
        "rb-chat-toolbar-floating bg-transparent shadow-none items-center justify-end "
        "w-full px-4 py-3 sticky top-0 z-10 gap-3"
    ):
        _toolbar = UIStyling.CHAT_HEADER_BUTTON
        # color=None — avoid Quasar color="primary" on dim state (reads bluish vs our maroon CSS).
        _btn_kw = {"color": None}
        _props = "unelevated no-caps"
        with ui.row().classes("items-center gap-3"):
            models_btn = ui.button("Menu", **_btn_kw).classes(_toolbar).props(_props)
            analyze_btn = ui.button("Chat", **_btn_kw).classes(_toolbar).props(_props)
            if on_show_history:
                history_btn = (
                    ui.button("History", on_click=on_show_history, **_btn_kw)
                    .classes(_toolbar)
                    .props(_props)
                )
            else:
                history_btn = (
                    ui.button(
                        "History",
                        on_click=lambda: ui.notify(
                            "No history available", type="info", classes="rb-notify-505759"
                        ),
                        **_btn_kw,
                    )
                    .classes(_toolbar)
                    .props(_props)
                )
            history_btn.visible = user_has_job_history()
            #i.button('New Conversation', on_click=on_new_conversation).classes(
            #    f'rb-brand-primary text-white {_btn_lg}'
            #)

    return models_btn, analyze_btn, history_btn

