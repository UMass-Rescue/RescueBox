"""
UI Operations — scroll, notify, and container updates for the chatbot and jobs UI.

**Scroll semantics (quick reference)**

- ``scroll_to_bottom`` — Chat assistant: scrolls the message scroller (``.rb-chat-messages-scroll``),
  latest job anchor (``.rb-job-result-anchor``), below-input area, and the window. Pass
  ``container.client`` from background jobs so JS runs in the correct tab.

- ``scroll_to_bottom_after_dom_update`` — ``await safe_container_update`` then ``scroll_to_bottom``
  plus delayed retries; use after ``show_results`` when DOM is still settling.

- ``scroll_document_to_bottom`` — Full-page routes (e.g. job details) without chat-specific nodes.

- ``scroll_form_into_view`` — One delayed pass with ``behavior: 'smooth'`` (legacy 120 ms defer).

- ``scroll_form_into_view_smooth`` — Single smooth ``scrollIntoView`` (pair with
  ``FormConfig.FORM_SCROLL_AFTER_REVEAL_DELAY_S`` so movement is a slow pan, not a snap).

- ``scroll_form_into_view_with_retries`` — Several instant passes (``behavior: 'auto'``);
  for pipelines where ``scroll_to_bottom`` timers compete; not ideal after a long intentional delay.

Safe UI operations also tolerate test environments (e.g. missing slot) where noted on each method.
"""

import logging
import asyncio
from typing import Optional

from nicegui import ui

logger = logging.getLogger(__name__)

# Shared by scroll_to_bottom; must use Client.run_javascript from background tasks (no UI context).
_SCROLL_TO_BOTTOM_JS = """
    (function() {
        function scrollPageToBottom() {
            const h = Math.max(
                document.body ? document.body.scrollHeight : 0,
                document.documentElement ? document.documentElement.scrollHeight : 0
            );
            window.scrollTo(0, h);
            if (document.documentElement) {
                document.documentElement.scrollTop = document.documentElement.scrollHeight;
            }
            if (document.body) {
                document.body.scrollTop = document.body.scrollHeight;
            }
        }
        function scrollChatPanels() {
            document.querySelectorAll('.rb-chat-messages-scroll').forEach((el) => {
                el.scrollTop = el.scrollHeight;
            });
        }
        function scrollLatestJobResultIntoView() {
            const anchors = document.querySelectorAll('.rb-job-result-anchor');
            if (!anchors.length) {
                return false;
            }
            const el = anchors[anchors.length - 1];
            try {
                el.scrollIntoView({ block: 'end', inline: 'nearest', behavior: 'auto' });
            } catch (e) {
                el.scrollIntoView(false);
            }
            return true;
        }
        function scrollBelowInputIntoView() {
            const below = document.querySelector('.rb-chat-below-input-area');
            if (below) {
                try {
                    below.scrollIntoView({ behavior: 'auto', block: 'end' });
                } catch (e) {
                    below.scrollIntoView(false);
                }
            }
        }
        function runScrollPass() {
            scrollLatestJobResultIntoView();
            scrollChatPanels();
            scrollBelowInputIntoView();
            scrollPageToBottom();
        }
        function runAfterLayout() {
            requestAnimationFrame(function() {
                requestAnimationFrame(runScrollPass);
            });
        }
        const delays = [0, 50, 150, 350, 700];
        delays.forEach(function(ms) {
            setTimeout(runAfterLayout, ms);
        });
    })();
"""

# Standalone pages (e.g. /jobs/{id}): scroll window and NiceGUI main content, not chat-specific nodes.
_SCROLL_DOCUMENT_TO_BOTTOM_JS = """
    (function() {
        function scrollPass() {
            const h = Math.max(
                document.body ? document.body.scrollHeight : 0,
                document.documentElement ? document.documentElement.scrollHeight : 0
            );
            window.scrollTo(0, h);
            if (document.documentElement) {
                document.documentElement.scrollTop = document.documentElement.scrollHeight;
            }
            if (document.body) {
                document.body.scrollTop = document.body.scrollHeight;
            }
            document.querySelectorAll('.nicegui-content').forEach(function(el) {
                try {
                    el.scrollTop = el.scrollHeight;
                } catch (e) {}
            });
            var qpage = document.querySelector('.q-page');
            if (qpage) {
                try {
                    qpage.scrollTop = qpage.scrollHeight;
                } catch (e) {}
            }
        }
        function run() {
            requestAnimationFrame(function() {
                requestAnimationFrame(scrollPass);
            });
        }
        [0, 80, 200, 500].forEach(function(ms) {
            setTimeout(run, ms);
        });
    })();
"""

# Scroll the active form (.rb-form-wrapper last) into view with several passes so we win over
# scroll_to_bottom's multi-delay JS (0–700ms), which otherwise pulls the viewport past the form.
# Use behavior "auto" on every pass: multiple "smooth" animations to the same node stack and read
# as a flickering / garbled viewport; instant snaps are stable and still retry as layout settles.
_SCROLL_FORM_INTO_VIEW_RETRIES_JS = """
    (function() {
        function scrollForm() {
            const forms = document.querySelectorAll('.rb-form-wrapper');
            const form = forms.length ? forms[forms.length - 1] : null;
            if (!form) {
                return;
            }
            try {
                form.scrollIntoView({ block: 'start', behavior: 'auto' });
            } catch (e) {
                try {
                    form.scrollIntoView(true);
                } catch (e2) {}
            }
        }
        function run() {
            requestAnimationFrame(function() {
                requestAnimationFrame(scrollForm);
            });
        }
        [0, 140, 360].forEach(function(ms) {
            setTimeout(run, ms);
        });
    })();
"""

# One smooth scroll — use after FORM_SCROLL_AFTER_REVEAL_DELAY_S (instant snap looks jarring).
_SCROLL_FORM_INTO_VIEW_SMOOTH_JS = """
    (function() {
        const forms = document.querySelectorAll('.rb-form-wrapper');
        const form = forms.length ? forms[forms.length - 1] : null;
        if (!form) {
            return;
        }
        try {
            form.scrollIntoView({ block: 'start', behavior: 'smooth' });
        } catch (e) {
            try {
                form.scrollIntoView(true);
            } catch (e2) {}
        }
    })();
"""


class UIOperations:
    """Safe UI operations that work in both normal and test environments."""

    @staticmethod
    async def safe_navigate_to(path: str, delay: float = 0.5):
        """Navigate to path with safe error handling for test environments."""
        try:
            ui.navigate.to(path)
            if delay > 0:
                await asyncio.sleep(delay)
        except RuntimeError as ui_error:
            if "slot cannot be determined" in str(ui_error):
                logger.debug("UI navigation skipped in test environment: %s", ui_error)
            else:
                raise

    @staticmethod
    def safe_notify(
        message: str,
        type: str = "info",
        timeout: Optional[int] = None,
        *,
        classes: str = "rb-notify-505759",
    ):
        """Show notification with safe error handling for test environments.

        ``classes`` defaults to medium-gray toasts (``rb-notify-505759``). Use ``rb-notify-a2aaad``
        for UMass light gray (PMS 429) background with dark text.

        With those skin classes, Quasar ``type`` (``info``, ``negative``, etc.) adds ``bg-info`` /
        ``bg-negative`` / … which often overrides the skin — so ``type`` is omitted and only the
        skin classes control appearance.
        """
        try:
            notify_type = type
            if classes and (
                "rb-notify-a2aaad" in classes or "rb-notify-505759" in classes
            ):
                if notify_type in ("info", "positive", "negative", "warning", "ongoing"):
                    notify_type = None
            kwargs: dict = {"classes": classes}
            if notify_type is not None:
                kwargs["type"] = notify_type
            if timeout:
                kwargs["timeout"] = timeout
            ui.notify(message, **kwargs)
        except RuntimeError as ui_error:
            if "slot cannot be determined" in str(ui_error):
                logger.debug("UI notification skipped in test environment: %s", ui_error)
            else:
                raise

    @staticmethod
    async def safe_container_update(container):
        """Update container with safe error handling for test environments."""
        try:
            container.update()
        except RuntimeError as ui_error:
            if "slot cannot be determined" in str(ui_error):
                logger.debug("Container update skipped in test environment: %s", ui_error)
            else:
                raise

    @staticmethod
    def scroll_to_bottom(client=None):
        """
        Scroll to the bottom of the chat area and the window.

        The main message list uses ``overflow-auto`` on a column (``.rb-chat-messages-scroll``);
        ``window.scrollTo`` alone does not move that inner scroll, which is especially visible
        in Plugins menu mode after a job completes.

        Re-run-after-history renders results under the input (``.rb-chat-below-input-area``), outside
        the message scroller; that block must be scrolled into view as well.

        After ``show_results``, the DOM may update a tick later than ``run_javascript``; we retry
        and prefer ``scrollIntoView`` on ``.rb-job-result-anchor`` so nested scroll parents update.

        **Important:** ``ui.run_javascript`` uses the current UI context's client. NiceGUI background
        tasks (e.g. job completion) have **no** slot context — pass ``container.client`` so the script
        runs in the correct browser tab.
        """
        if client is not None:
            try:
                client.run_javascript(_SCROLL_TO_BOTTOM_JS)
                return
            except Exception as ex:
                logger.debug("scroll_to_bottom: client.run_javascript failed: %s", ex)
        try:
            ui.run_javascript(_SCROLL_TO_BOTTOM_JS)
        except Exception as ex:
            logger.debug("scroll_to_bottom: ui.run_javascript failed: %s", ex)

    @staticmethod
    def scroll_document_to_bottom(client=None):
        """
        Scroll the browser window and NiceGUI layout content to the bottom.

        Use on full-page routes (e.g. job details) where chat-specific selectors do not apply.
        """
        if client is not None:
            try:
                client.run_javascript(_SCROLL_DOCUMENT_TO_BOTTOM_JS)
                return
            except Exception as ex:
                logger.debug("scroll_document_to_bottom: client.run_javascript failed: %s", ex)
        try:
            ui.run_javascript(_SCROLL_DOCUMENT_TO_BOTTOM_JS)
        except Exception as ex:
            logger.debug("scroll_document_to_bottom: ui.run_javascript failed: %s", ex)

    @staticmethod
    async def scroll_to_bottom_after_dom_update(container=None):
        """
        Flush container updates (NiceGUI → client), then scroll with retries.

        Call after ``show_results`` so ``.rb-job-result-anchor`` exists in the DOM before scroll runs.
        """
        client = None
        try:
            if container is not None:
                await UIOperations.safe_container_update(container)
                client = container.client
        except Exception:
            try:
                if container is not None:
                    client = container.client
            except Exception:
                pass
        UIOperations.scroll_to_bottom(client=client)
        for delay in (0.15, 0.45, 1.0):
            c = client
            ui.timer(delay, lambda c=c: UIOperations.scroll_to_bottom(client=c), once=True)

    @staticmethod
    def scroll_form_into_view(client=None):
        """Scroll the active form (last ``.rb-form-wrapper``) into view near the top of the viewport."""
        _js = """
            setTimeout(() => {
                const forms = document.querySelectorAll('.rb-form-wrapper');
                const form = forms.length ? forms[forms.length - 1] : null;
                if (form) {
                    try {
                        form.scrollIntoView({ block: 'start', behavior: 'smooth' });
                    } catch (e) {
                        try { form.scrollIntoView(true); } catch (e2) {}
                    }
                }
            }, 120);
        """
        if client is not None:
            try:
                client.run_javascript(_js)
                return
            except Exception as ex:
                logger.debug("scroll_form_into_view: client.run_javascript failed: %s", ex)
        try:
            ui.run_javascript(_js)
        except Exception as ex:
            logger.debug("scroll_form_into_view: ui.run_javascript failed: %s", ex)

    @staticmethod
    def scroll_form_into_view_smooth(client=None):
        """
        Smoothly scroll the last ``.rb-form-wrapper`` into view (single animation).

        Use after ``FormConfig.FORM_SCROLL_AFTER_REVEAL_DELAY_S`` so the motion is a slow pan,
        not an instant jump (``scroll_form_into_view_with_retries`` uses ``behavior: 'auto'``).
        """
        if client is not None:
            try:
                client.run_javascript(_SCROLL_FORM_INTO_VIEW_SMOOTH_JS)
                return
            except Exception as ex:
                logger.debug("scroll_form_into_view_smooth: client.run_javascript failed: %s", ex)
        try:
            ui.run_javascript(_SCROLL_FORM_INTO_VIEW_SMOOTH_JS)
        except Exception as ex:
            logger.debug("scroll_form_into_view_smooth: ui.run_javascript failed: %s", ex)

    @staticmethod
    def scroll_form_into_view_with_retries(client=None):
        """
        Scroll the active form into view with several delayed passes.

        Use after multi-tool or other flows where ``scroll_to_bottom`` may run on timers
        and override a single ``scrollIntoView`` call.
        """
        if client is not None:
            try:
                client.run_javascript(_SCROLL_FORM_INTO_VIEW_RETRIES_JS)
                return
            except Exception as ex:
                logger.debug("scroll_form_into_view_with_retries: client.run_javascript failed: %s", ex)
        try:
            ui.run_javascript(_SCROLL_FORM_INTO_VIEW_RETRIES_JS)
        except Exception as ex:
            logger.debug("scroll_form_into_view_with_retries: ui.run_javascript failed: %s", ex)
