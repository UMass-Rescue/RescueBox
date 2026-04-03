"""
Global readability CSS: Quasar notifications and scoped chat input.

The app sets ``body { font-size: 0.8rem !important; }`` on several pages; we raise
sizes for toasts and the chat composer without editing every screen by hand.
Inject once at startup (see ``main.py``).
"""

from __future__ import annotations

import logging

from nicegui import ui

logger = logging.getLogger(__name__)

_READABILITY_CSS_DONE = False


def inject_global_readability_css() -> None:
    """Inject shared styles once (``shared=True``) for all clients."""
    global _READABILITY_CSS_DONE
    if _READABILITY_CSS_DONE:
        return
    _READABILITY_CSS_DONE = True
    ui.add_head_html(
        """
        <style>
        /* --- Quasar notifications (ui.notify everywhere) --- */
        .q-notifications__list .q-notification,
        .q-notification {
            font-size: 1rem !important;
            line-height: 1.5 !important;
        }
        .q-notification__message {
            font-size: 1rem !important;
            line-height: 1.5 !important;
        }
        .q-notification__caption {
            font-size: 0.9375rem !important;
        }
        .q-notification .q-btn {
            font-size: 0.9375rem !important;
        }

        /* --- Chat input strip (parent has .rb-chat-input-area) --- */
        .rb-chat-input-area .q-field__label {
            font-size: 1rem !important;
        }
        .rb-chat-input-area .q-textarea .q-field__native,
        .rb-chat-input-area textarea.q-field__native {
            font-size: 1rem !important;
            line-height: 1.5 !important;
            padding: 10px 12px !important;
            min-height: 56px !important;
        }
        .rb-chat-input-area .q-textarea .q-field__control {
            min-height: 56px !important;
        }
        .rb-chat-input-area .q-btn {
            font-size: 1rem !important;
            padding: 8px 18px !important;
            min-height: 40px !important;
        }
        .rb-chat-input-area .text-gray-600 {
            font-size: 1rem !important;
        }
        </style>
        """,
        shared=True,
    )
    logger.debug("Global readability CSS injected (notifications + .rb-chat-input-area)")
