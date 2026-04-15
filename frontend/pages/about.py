"""About: app metadata and License & Copyright documents."""

from __future__ import annotations

import logging

from nicegui import ui
from starlette.requests import Request

from frontend.components.about.license_documents import render_license_documents_section
from frontend.components.shared import create_navbar
from frontend.config import (
    ABOUT_AUTHORS,
    ABOUT_REPO_DESKTOP_URL,
    ABOUT_REPO_URL,
    APP_TITLE,
    APP_VERSION,
)

logger = logging.getLogger(__name__)


@ui.page("/about")
async def about_page(request: Request):
    from frontend.utils.theme import apply_saved_theme

    apply_saved_theme()
    create_navbar()

    with ui.column().classes("w-full max-w-full min-w-0 container mx-auto p-4 pb-16"):
        ui.label("About").classes("text-2xl font-bold mb-6")

        with ui.card().classes("w-full max-w-3xl mb-10 p-6"):
            ui.label("Application").classes("text-lg font-semibold mb-4")
            _rows = (
                ("name", APP_TITLE, False),
                ("version", APP_VERSION, False),
                ("authors", ABOUT_AUTHORS, False),
                ("repository", ABOUT_REPO_URL, True),
            )
            for key, val, is_url in _rows:
                with ui.row().classes(
                    "w-full gap-4 py-2 border-b border-gray-100 last:border-0 items-start"
                ):
                    ui.label(f"{key}").classes(
                        "text-sm font-mono text-gray-600 shrink-0 w-44 sm:w-52"
                    )
                    if is_url and val.startswith("http"):
                        ui.link(val, val, new_tab=True).classes(
                            "text-sm text-blue-700 break-all min-w-0 flex-1"
                        )
                    else:
                        ui.label(val).classes(
                            "text-sm text-gray-900 break-words flex-1 min-w-0"
                        )

        render_license_documents_section(request, page_path="/about")

    logger.debug("About page rendered")
