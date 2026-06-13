"""Shared NiceGUI scroll/notify helpers for chat and related pages."""

from __future__ import annotations

import asyncio
import logging

from nicegui import ui

from frontend.utils import notify_error, notify_info, notify_success, notify_warning
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)


class UIOperations:
    """Scroll, notify, and container update helpers for the chatbot and job UI."""

    @staticmethod
    def _run_js(client, js: str) -> None:
        try:
            if client:
                client.run_javascript(js)
            else:
                ui.run_javascript(js)
        except UI_RENDER_ERRORS:
            pass

    @staticmethod
    def scroll_to_bottom(client=None) -> None:
        UIOperations._run_js(
            client,
            "window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});",
        )

    @staticmethod
    def scroll_document_to_bottom(client=None) -> None:
        """Instant scroll (used on job details and similar full-page views)."""
        try:
            (client or ui).run_javascript(
                "window.scrollTo(0, document.body.scrollHeight)"
            )
        except UI_RENDER_ERRORS:
            pass

    @staticmethod
    def scroll_form_into_view(client=None) -> None:
        js = (
            "const el = document.querySelector('.rb-form-wrapper'); "
            "if(el) el.scrollIntoView({behavior: 'smooth', block: 'center'});"
        )
        UIOperations._run_js(client, js)

    @staticmethod
    def scroll_form_into_view_with_retries(client=None) -> None:
        for delay in (0.1, 0.3, 0.7):
            ui.timer(
                delay,
                lambda c=client: UIOperations.scroll_form_into_view(c),
                once=True,
            )

    @staticmethod
    def safe_notify(message: str, notify_type: str = "info", **kwargs) -> None:
        try:
            normalized = (notify_type or "info").lower()
            if normalized in ("success", "positive"):
                notify_success(message)
            elif normalized in ("error", "negative"):
                notify_error(message)
            elif normalized == "warning":
                notify_warning(message)
            elif normalized == "info":
                notify_info(message)
            else:
                ui.notify(message, type=notify_type, **kwargs)
        except UI_RENDER_ERRORS:
            pass

    @staticmethod
    async def safe_container_update(container) -> None:
        try:
            if hasattr(container, "update"):
                container.update()
            await asyncio.sleep(0.01)
        except UI_RENDER_ERRORS:
            pass

    @staticmethod
    async def scroll_to_bottom_after_dom_update(client=None) -> None:
        await asyncio.sleep(0.05)
        UIOperations.scroll_to_bottom(client)
