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

RESCUE_LAB_URL = "https://www.rescue-lab.org/"


@ui.page("/about")
async def about_page(request: Request):
    from frontend.utils.theme import apply_saved_theme

    apply_saved_theme()
    create_navbar()

    with ui.column().classes("w-full max-w-full min-w-0 container mx-auto p-4 pb-16"):
        ui.label("About").classes("text-3xl font-bold text-zinc-900 mb-6")

        with ui.card().classes(
            "w-full max-w-3xl mb-10 p-6 bg-white border border-zinc-300 rounded-xl shadow-sm"
        ):
            ui.label("Application").classes("text-lg font-semibold text-[#505759] mb-4")
            _rows = (
                ("name", APP_TITLE, False),
                ("version", APP_VERSION, False),
                ("authors", ABOUT_AUTHORS, False),
                ("rescue lab website", RESCUE_LAB_URL, True),
                ("repository", ABOUT_REPO_URL, True),
            )
            for key, val, is_url in _rows:
                with ui.row().classes(
                    "w-full gap-4 py-2 border-b border-zinc-200 last:border-0 items-start"
                ):
                    ui.label(f"{key}").classes(
                        "text-sm font-mono text-zinc-600 shrink-0 w-44 sm:w-52"
                    )
                    if is_url and val.startswith("http"):
                        ui.link(val, val, new_tab=True).classes(
                            "text-sm text-[#505759] hover:text-[#3d4442] hover:underline "
                            "break-all min-w-0 flex-1"
                        )
                    else:
                        ui.label(val).classes(
                            "text-sm text-zinc-900 break-words flex-1 min-w-0"
                        )

        render_license_documents_section(request, page_path="/about")

    logger.debug("About page rendered")
