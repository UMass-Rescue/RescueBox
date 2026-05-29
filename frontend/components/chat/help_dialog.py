import logging
from typing import Optional

from nicegui import ui

from frontend.design_tokens import Design

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Explicit element sizes + ! so Quasar / dialog defaults do not shrink markdown
# (same idea as ``_MD_MODAL`` in image_summary_results_view).
_HELP_MARKDOWN_CLASSES = (
    "prose prose-zinc max-w-none text-zinc-900 "
    "[&_p]:!text-xl [&_p]:!leading-relaxed [&_p]:my-3 "
    "[&_li]:!text-xl [&_li]:!leading-relaxed [&_ul]:my-3 [&_ol]:my-3 "
    "[&_blockquote]:!text-lg [&_blockquote]:border-l-4 [&_blockquote]:pl-4 "
    "[&_pre]:!text-base [&_pre]:leading-relaxed [&_pre]:whitespace-pre-wrap "
    "[&_pre]:p-3 [&_pre]:bg-zinc-100 [&_pre]:rounded "
    "[&_code]:!text-base [&_h1]:!text-3xl [&_h2]:!text-2xl [&_h3]:!text-2xl "
    "[&_h4]:!text-2xl [&_h5]:!text-xl [&_strong]:font-semibold [&_div]:!text-xl "
    "[&_a]:!text-xl [&_a]:underline"
)


def show_help_dialog(help_text: str, title: Optional[str] = "RescueBox Help") -> None:
    """
    Show help text in a large dialog optimized for readability.
    """
    try:
        with ui.dialog() as dialog, ui.card().classes(Design.PANEL_SHELL_CARD_WIDE):
            with ui.row().classes(Design.PANEL_SHELL_HEADER):
                ui.label(title or "Help").classes(Design.PANEL_SHELL_HEADER_TITLE)
                ui.button(icon="close", on_click=dialog.close, color=None).props(
                    "flat round dense"
                ).classes(Design.PANEL_SHELL_HEADER_ICON)

            # Plain overflow column — q-scroll-area + Tailwind flex/overflow from
            # PANEL_SHELL_BODY often yields zero-height content in dialogs.
            with ui.column().classes(
                "w-full flex-1 min-h-0 max-h-[calc(95vh-9rem)] overflow-y-auto "
                "bg-white p-6 gap-4"
            ):
                ui.markdown(help_text or "No help available.").classes(
                    _HELP_MARKDOWN_CLASSES
                    + " leading-relaxed whitespace-pre-wrap w-full min-w-0"
                )
            # Must open before leaving the ``with`` block — otherwise the dialog can
            # serialize without body content and show empty.
            dialog.open()
    except Exception as e:
        logger.exception("Failed to open help dialog: %s", e)
