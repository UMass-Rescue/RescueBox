"""NiceGUI route registration and chatbot page entrypoints."""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import parse_qs, urlparse

from nicegui import context, ui

from frontend.chatbot.config import ChatbotConfig
from frontend.components.shared import create_navbar
from frontend.pages.chatbot.chat_page import ChatbotPage
from frontend.pages.page_shell import COMPACT_TOOLBAR_HEAD_HTML
from frontend.components.ui_exceptions import UI_RENDER_ERRORS
from frontend.utils import (
    apply_saved_theme,
    ensure_user_id,
    get_conversation_to_load,
)

logger = logging.getLogger(__name__)


def _query_params_from_client(client) -> Optional[dict]:
    req = getattr(client, "request", None)
    if req is None or not hasattr(req, "query_params"):
        return None
    try:
        qp = dict(req.query_params)
    except UI_RENDER_ERRORS:
        return None
    return qp if qp else None


def _extract_chatbot_query_from_client() -> dict:
    """
    When NiceGUI does not inject ?load_conversation / ?rerun into the page handler,
    parse them from the Starlette request or client page URL.
    """
    try:
        client = getattr(context, "client", None)
        if client:
            qp = _query_params_from_client(client)
            if qp is not None:
                return qp

        if not client:
            return {}
        page = getattr(client, "page", None)
        url = ""
        if page is not None:
            url = str(getattr(page, "url", None) or getattr(page, "path", None) or "")
        if not url:
            return {}
        q = parse_qs(urlparse(url).query)
        return {k: v[0] for k, v in q.items() if v}
    except UI_RENDER_ERRORS:
        return {}


async def handle_rerun_parameter(message_id: str) -> None:
    """Re-run a persisted tool message (``?rerun=`` query or in-chat Re-run button)."""
    chatbot = ChatbotPage.get_instance()
    if not chatbot:
        ui.notify("Chatbot not ready to rerun tool.", type="negative")
        return
    await chatbot.handle_rerun_tool(message_id)


@ui.page("/chatbot")
async def chatbot_page(
    load_conversation: Optional[str] = None, rerun: Optional[str] = None
):
    if ensure_user_id() is None:
        return

    apply_saved_theme()
    create_navbar()
    ui.add_head_html(COMPACT_TOOLBAR_HEAD_HTML)

    chatbot = ChatbotPage()
    await chatbot.render()

    extracted = _extract_chatbot_query_from_client()
    eff_rerun = rerun or extracted.get("rerun")
    eff_load = load_conversation or extracted.get("load_conversation")

    if eff_rerun:
        await handle_rerun_parameter(eff_rerun)
    elif eff_load:
        await chatbot.handle_conversation_select(eff_load)
    else:
        stored = get_conversation_to_load()
        if stored and stored.get("conversation_id"):
            await chatbot.load_conversation_from_data(stored)


async def create_chat_ui(config: Optional[ChatbotConfig] = None):
    chatbot = ChatbotPage(config)
    await chatbot.render()
    return chatbot
