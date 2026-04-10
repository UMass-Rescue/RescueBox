"""
UI Operations.

Safe UI operations that work in both normal and test environments.
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
    def safe_notify(message: str, type: str = 'info', timeout: Optional[int] = None):
        """Show notification with safe error handling for test environments."""
        try:
            if timeout:
                ui.notify(message, type=type, timeout=timeout)
            else:
                ui.notify(message, type=type)
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
    def scroll_form_into_view():
        """Scroll the displayed form into view (to top of viewport) instead of page bottom."""
        ui.run_javascript("""
            setTimeout(() => {
                const forms = document.querySelectorAll('.rb-form-wrapper');
                const form = forms.length ? forms[forms.length - 1] : null;
                if (form) {
                    form.scrollIntoView({ block: 'start', behavior: 'smooth' });
                } else {
                    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                }
            }, 150);
        """)
