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

_READABILITY_CSS_STATE = {"done": False}


def inject_global_readability_css() -> None:
    """Inject shared styles once (``shared=True``) for all clients."""
    if _READABILITY_CSS_STATE["done"]:
        return
    _READABILITY_CSS_STATE["done"] = True
    ui.add_head_html(
        """
        <link rel="icon" href="/icons/favicon.png?v=5" type="image/png">
        <style>
        /* --- Quasar notifications (ui.notify everywhere) --- */
        .q-notifications__list .q-notification,
        .q-notification {
            font-size: 1rem !important;
            line-height: 1.5 !important;
        }
        .q-notifications__list .q-notification .q-notification__message,
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
        /* Optional toast skin (classes="rb-notify-1e293b" on ui.notify).
           Brand charcoal #1e293b reserved for icons / accents; panel is light so body text stays dark (readable).
           Quasar Notify builds the root as: q-notification … bg-{color} text-{textColor} … + your classes;
           type=warning adds bg-warning + text-dark — override both.
           Use .q-notifications … (not only .q-notifications__list) so portaled / transition wrappers still match. */
        .q-notifications .q-notification.rb-notify-1e293b,
        .q-notifications .q-notification.rb-notify-1e293b.bg-positive,
        .q-notifications .q-notification.rb-notify-1e293b.bg-negative,
        .q-notifications .q-notification.rb-notify-1e293b.bg-warning,
        .q-notifications .q-notification.rb-notify-1e293b.bg-info,
        .q-notifications .q-notification.rb-notify-1e293b.bg-primary,
        .q-notifications .q-notification.rb-notify-1e293b.bg-grey-8,
        .q-notifications .q-notification.rb-notify-1e293b.text-dark,
        .q-notifications .q-notification.rb-notify-1e293b.text-white,
        div.q-notifications__list div.q-notification.rb-notify-1e293b,
        div.q-notifications__list div.q-notification.rb-notify-1e293b.bg-positive,
        div.q-notifications__list div.q-notification.rb-notify-1e293b.bg-negative,
        div.q-notifications__list div.q-notification.rb-notify-1e293b.bg-warning,
        div.q-notifications__list div.q-notification.rb-notify-1e293b.bg-info,
        div.q-notifications__list div.q-notification.rb-notify-1e293b.bg-primary,
        div.q-notifications__list div.q-notification.rb-notify-1e293b.bg-grey-8,
        div.q-notifications__list div.q-notification.rb-notify-1e293b.text-dark,
        div.q-notifications__list div.q-notification.rb-notify-1e293b.text-white {
            background: #e4e7e9 !important;
            background-color: #e4e7e9 !important;
            background-image: none !important;
            color: #18181b !important;
            box-shadow: 0 1px 5px rgba(0, 0, 0, 0.2), 0 2px 2px rgba(0, 0, 0, 0.14),
                0 3px 1px -2px rgba(0, 0, 0, 0.12) !important;
        }
        .q-notifications .q-notification.rb-notify-1e293b .q-notification__message,
        .q-notifications .q-notification.rb-notify-1e293b .q-notification__caption,
        div.q-notifications__list div.q-notification.rb-notify-1e293b .q-notification__message,
        div.q-notifications__list div.q-notification.rb-notify-1e293b .q-notification__caption {
            color: #18181b !important;
        }
        .q-notifications .q-notification.rb-notify-1e293b .q-icon,
        div.q-notifications__list div.q-notification.rb-notify-1e293b .q-icon {
            color: #1e293b !important;
        }
        .q-notifications .q-notification.rb-notify-1e293b .q-notification__actions .q-btn,
        div.q-notifications__list div.q-notification.rb-notify-1e293b .q-notification__actions .q-btn {
            color: #18181b !important;
        }
        .q-notifications .q-notification.rb-notify-1e293b .q-notification__progress,
        div.q-notifications__list div.q-notification.rb-notify-1e293b .q-notification__progress {
            background: rgba(24, 24, 27, 0.22) !important;
            color: #18181b !important;
        }

        /* Light gray toast (PMS 429 #a2aaad) — dark text for contrast (same as .rb-select-directory-header). */
        .q-notifications .q-notification.rb-notify-a2aaad,
        .q-notifications .q-notification.rb-notify-a2aaad.bg-positive,
        .q-notifications .q-notification.rb-notify-a2aaad.bg-negative,
        .q-notifications .q-notification.rb-notify-a2aaad.bg-warning,
        .q-notifications .q-notification.rb-notify-a2aaad.bg-info,
        .q-notifications .q-notification.rb-notify-a2aaad.bg-primary,
        .q-notifications .q-notification.rb-notify-a2aaad.bg-grey-8,
        .q-notifications .q-notification.rb-notify-a2aaad.text-dark,
        .q-notifications .q-notification.rb-notify-a2aaad.text-white,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad.bg-positive,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad.bg-negative,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad.bg-warning,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad.bg-info,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad.bg-primary,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad.bg-grey-8,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad.text-dark,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad.text-white {
            background: #a2aaad !important;
            background-color: #a2aaad !important;
            background-image: none !important;
            color: #18181b !important;
            box-shadow: 0 1px 5px rgba(0, 0, 0, 0.2), 0 2px 2px rgba(0, 0, 0, 0.14),
                0 3px 1px -2px rgba(0, 0, 0, 0.12) !important;
        }
        .q-notifications .q-notification.rb-notify-a2aaad .q-notification__message,
        .q-notifications .q-notification.rb-notify-a2aaad .q-notification__caption,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad .q-notification__message,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad .q-notification__caption {
            color: #18181b !important;
        }
        .q-notifications .q-notification.rb-notify-a2aaad .q-icon,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad .q-icon {
            color: #1e293b !important;
        }
        .q-notifications .q-notification.rb-notify-a2aaad .q-notification__actions .q-btn,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad .q-notification__actions .q-btn {
            color: #18181b !important;
        }
        .q-notifications .q-notification.rb-notify-a2aaad .q-notification__progress,
        div.q-notifications__list div.q-notification.rb-notify-a2aaad .q-notification__progress {
            background: rgba(24, 24, 27, 0.25) !important;
            color: #18181b !important;
        }

        /* --- RescueBox brand colors (UMass Maroon #881c1c for primary actions app-wide)
            Default ui.button uses Quasar color=primary; setting --q-primary on :root makes every
            primary-styled control UMass Maroon. .rb-brand-primary keeps explicit fill/hover for markers.
            Navbar uses Dark Charcoal #1c1c1c via .rb-brand-nav. --- */
        :root {
            --q-primary: #881c1c !important;
        }

        /* Global premium light theme overrides for body and Quasar components */
        body {
            background-color: #f8fafc !important; /* Slate 50 - soft off-white background */
            color: #0f172a !important; /* Slate 900 - dark text */
        }
        .q-layout, .q-page-container {
            background-color: #f8fafc !important;
        }
        .q-card {
            background-color: #ffffff !important; /* Pure white cards */
            color: #0f172a !important;
            border: 1px solid #e2e8f0 !important; /* Slate 200 - thin elegant border */
            box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05), 0 1px 2px -1px rgb(0 0 0 / 0.05) !important;
        }
        .q-field__control {
            background-color: #ffffff !important;
            color: #0f172a !important;
        }
        .q-field__native, .q-field__prefix, .q-field__suffix, .q-field__input {
            color: #0f172a !important;
        }
        .q-field__label {
            color: #64748b !important; /* Slate 500 */
        }
        .q-field--focused .q-field__label {
            color: #881c1c !important;
        }
        .q-dialog__inner .q-card {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #e2e8f0 !important;
        }
        .q-menu {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid #e2e8f0 !important;
        }
        .q-item {
            color: #0f172a !important;
        }
        .q-item:hover {
            background-color: #f1f5f9 !important; /* Slate 100 on hover */
        }

        .q-header.rb-brand-nav {
            --q-primary: #881c1c !important;
            background-color: #881c1c !important;
            background-image: none !important;
            color: #ffffff !important;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1) !important;
        }
        .q-header.rb-brand-nav .q-btn,
        .q-header.rb-brand-nav .q-icon,
        .q-header.rb-brand-nav a,
        .q-header.rb-brand-nav span,
        .q-header.rb-brand-nav div {
            color: #ffffff !important;
        }
        button.q-btn.rb-brand-primary,
        a.q-btn.rb-brand-primary,
        .q-btn.rb-brand-primary {
            --q-primary: #881c1c !important;
            background-color: #881c1c !important;
            color: #fff !important;
        }
        button.q-btn.rb-brand-primary:hover,
        a.q-btn.rb-brand-primary:hover,
        .q-btn.rb-brand-primary:hover,
        button.q-btn.rb-brand-primary:focus-visible,
        a.q-btn.rb-brand-primary:focus-visible,
        .q-btn.rb-brand-primary:focus-visible {
            --q-primary: #6a1616 !important;
            background-color: #6a1616 !important;
            color: #fff !important;
        }
        .q-btn.rb-brand-primary .q-icon {
            color: inherit;
        }
        /* UMass Maroon #881c1c — Browse, Cancel, secondary solid actions */
        button.q-btn.rb-btn-medium-gray,
        a.q-btn.rb-btn-medium-gray,
        .q-btn.rb-btn-medium-gray {
            --q-primary: #881c1c !important;
            background-color: #881c1c !important;
            color: #fff !important;
            border-color: transparent !important;
        }
        button.q-btn.rb-btn-medium-gray:hover,
        a.q-btn.rb-btn-medium-gray:hover,
        .q-btn.rb-btn-medium-gray:hover,
        button.q-btn.rb-btn-medium-gray:focus-visible,
        a.q-btn.rb-btn-medium-gray:focus-visible,
        .q-btn.rb-btn-medium-gray:focus-visible {
            --q-primary: #6a1616 !important;
            background-color: #6a1616 !important;
            color: #fff !important;
        }
        .q-btn.rb-btn-medium-gray .q-icon {
            color: inherit;
        }
        .rb-brand-step-current {
            background-color: #881c1c !important;
        }

        /* Chat mode / Plugins mode badge — q-badge does not always honor :root --q-primary */
        .q-badge.rb-chat-mode-badge,
        span.q-badge.rb-chat-mode-badge {
            background-color: #881c1c !important;
            color: #fff !important;
        }

        /* Select Directory dialog header — UMass Light Gray #a2aaad (PMS 429) */
        .rb-select-directory-header {
            background-color: #a2aaad !important;
            background-image: none !important;
            color: #18181b !important;
        }
        .rb-select-directory-header .q-icon {
            color: #1e293b !important;
        }

        /* Job Text Result card: no forced fill (inherit page / theme) */
        .q-card.rb-job-text-result-card,
        .rb-job-text-result-card.q-card {
            background-color: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
        }
        /* Browse Plugins (/models): Light Gray surface + UMass Maroon #881c1c border */
        .q-card.rb-models-plugin-card,
        .rb-models-plugin-card.q-card {
            background-color: #e4e4e7 !important;
            background-image: none !important;
            border: 2px solid #881c1c !important;
            box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.08) !important;
        }
        /* Text Result header: no filled band (inherits page / card surface) */
        .rb-job-text-result-card .rb-job-text-result-header {
            background-color: transparent !important;
            background-image: none !important;
            color: #18181b !important;
        }
        .rb-job-text-result-card .rb-job-text-result-header .q-icon {
            color: #3f3f46 !important;
        }

        /* Chatbot Menu/Chat/History: transparent strip behind solid Steel Blue buttons */
        .rb-chat-toolbar-floating {
            background: transparent !important;
            background-color: transparent !important;
        }
        /* Chatbot Tab Buttons (Menu, Chat, History) */
        .q-btn.rb-chatbot-tab-btn {
            background-color: #f1f5f9 !important; /* bg-slate-100 */
            color: #334155 !important; /* text-slate-700 */
            transition: all 0.2s ease-in-out !important;
        }
        .q-btn.rb-chatbot-tab-btn:hover {
            background-color: #e2e8f0 !important; /* bg-slate-200 */
            color: #334155 !important; /* text-slate-700 */
        }
        /* Active state */
        .q-btn.rb-chatbot-tab-btn.rb-tab-active {
            background-color: #881c1c !important; /* UMass Maroon */
            color: #ffffff !important; /* white text */
        }
        .q-btn.rb-chatbot-tab-btn.rb-tab-active:hover {
            background-color: #6a1616 !important; /* Darker Maroon hover */
            color: #ffffff !important; /* white text */
        }
        /* Ensure icons and text inside follow the color and disable focus helper */
        .q-btn.rb-chatbot-tab-btn .q-icon,
        .q-btn.rb-chatbot-tab-btn span {
            color: inherit !important;
        }
        .q-btn.rb-chatbot-tab-btn .q-focus-helper {
            display: none !important;
        }

        /* --- Chat input strip (parent has .rb-chat-input-area) --- */
        .rb-chat-input-area .q-field__label {
            font-size: 1rem !important;
        }
        .rb-image-summary-search-field .q-field__marginal .q-icon,
        .rb-image-summary-search-field .q-field__append .q-icon {
            color: #1e293b !important;
        }

        /* Case Notes field specific overrides to ensure no blue/indigo remains */
        .rb-case-notes-field .q-field__label,
        .rb-case-notes-field.q-field--float .q-field__label {
            color: #1e293b !important;
        }
        .rb-case-notes-field.q-field--focused .q-field__label {
            color: #881c1c !important;
        }
        .rb-case-notes-field.q-field--outlined .q-field__control:before {
            border-color: #d4d4d8 !important;
        }
        .rb-case-notes-field.q-field--outlined:hover .q-field__control:before {
            border-color: #1e293b !important;
        }
        .rb-case-notes-field.q-field--focused .q-field__control:after {
            border-color: #881c1c !important;
            border-width: 2px !important;
        }
        .rb-case-notes-field .q-field__native, .rb-case-notes-field textarea {
            color: #0f172a !important;
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
        .rb-chat-input-area .text-zinc-600 {
            font-size: 1rem !important;
        }
        /* Grey out composer (textarea + send) while pending; forms under input_area stay visible/interactive */
        .rb-chat-composer-core.rb-chat-input-pending-only {
            opacity: 0.5 !important;
            pointer-events: none !important;
            filter: grayscale(0.8) !important;
        }
        </style>
        """,
        shared=True,
    )
    logger.debug(
        "Global readability CSS injected (notifications + .rb-chat-input-area)"
    )
