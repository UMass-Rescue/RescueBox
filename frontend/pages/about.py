"""About: app metadata and License & Copyright documents."""

from __future__ import annotations

import logging

from nicegui import ui
from starlette.requests import Request

from frontend.components.about import render_license_documents_section
from frontend.components.shared import create_navbar
from frontend.config import (
    ABOUT_AUTHORS,
    ABOUT_REPO_URL,
    APP_TITLE,
    APP_VERSION,
)

logger = logging.getLogger(__name__)

RESCUE_LAB_URL = "https://www.rescue-lab.org/"


@ui.page("/about")
async def about_page(request: Request):
    from frontend.utils import apply_saved_theme

    apply_saved_theme()
    create_navbar()

    with ui.column().classes("container mx-auto px-4 sm:px-8 py-8 w-full max-w-6xl pb-16 gap-6"):
        # Hero Header Card
        with ui.card().classes(
            "w-full p-6 sm:p-8 bg-gradient-to-br from-slate-900 via-[#1c1c1c] to-slate-900 "
            "text-white rounded-2xl shadow-lg border border-slate-800 relative overflow-hidden"
        ):
            # Decorative background pattern/overlay
            ui.element("div").classes(
                "absolute -right-10 -bottom-10 w-40 h-40 bg-[#881c1c]/20 rounded-full blur-3xl"
            )
            with ui.row().classes("items-center gap-4 w-full relative z-10"):
                ui.icon("info", size="2.5rem").classes("text-[#881c1c]")
                with ui.column().classes("gap-1 flex-1"):
                    ui.label("About RescueBox").classes("text-2xl sm:text-3xl font-extrabold tracking-tight")
                    ui.label(
                        "An advanced, AI-powered forensic and investigative platform designed for deep data analysis, "
                        "media processing, and intelligence gathering."
                    ).classes("text-slate-300 text-sm sm:text-base max-w-3xl leading-relaxed")

        # Two-Column Layout
        with ui.grid().classes("w-full grid-cols-1 lg:grid-cols-3 gap-6 items-start"):
            # Left Column (System Info & Licenses) - Takes 2 cols on large screens
            with ui.column().classes("lg:col-span-2 w-full gap-6"):
                # System Info Card
                with ui.card().classes(
                    "w-full p-6 bg-white border border-slate-200 rounded-2xl shadow-sm border-t-4 border-t-[#881c1c]"
                ):
                    ui.label("System Information").classes("text-xl font-bold text-slate-800 mb-4")
                    
                    _system_rows = (
                        ("Application Name", APP_TITLE, "label", False),
                        ("Software Version", f"v{APP_VERSION}", "tag", False),
                        ("Core Developers", ABOUT_AUTHORS, "people", False),
                        ("Official Repository", ABOUT_REPO_URL, "code", True),
                    )
                    
                    with ui.column().classes("w-full gap-3"):
                        for label_text, val, icon_name, is_url in _system_rows:
                            with ui.row().classes(
                                "w-full gap-4 py-3 border-b border-slate-100 last:border-0 items-center hover:bg-slate-50/50 px-2 rounded-lg transition-colors"
                            ):
                                ui.icon(icon_name, size="sm").classes("text-[#881c1c] shrink-0")
                                with ui.column().classes("gap-0.5 flex-1 min-w-0"):
                                    ui.label(label_text).classes("text-xs font-semibold text-slate-400 uppercase tracking-wider")
                                    if is_url and val.startswith("http"):
                                        ui.link(val, val, new_tab=True).classes(
                                            "text-sm font-medium text-[#881c1c] hover:underline break-all min-w-0"
                                        )
                                    else:
                                        ui.label(val).classes("text-sm font-semibold text-slate-800 break-words")

                # Licenses Section
                with ui.column().classes("w-full"):
                    render_license_documents_section(request, page_path="/about")

            # Right Column (Sponsor & Quick Actions) - Takes 1 col
            with ui.column().classes("w-full gap-6"):
                # RescueLab Sponsor Card
                with ui.card().classes(
                    "w-full p-6 bg-white border border-slate-200 rounded-2xl shadow-sm "
                    "flex flex-col items-center text-center gap-4 border-t-4 border-t-[#881c1c]"
                ):
                    ui.label("Research & Sponsorship").classes("text-sm font-bold text-slate-400 uppercase tracking-wider self-start")
                    ui.element("img").props("src=/icons/rb.webp alt=\"RescueLab Logo\"").classes("h-16 object-contain my-2")
                    with ui.column().classes("gap-1 items-center"):
                        ui.label("RescueLab").classes("text-lg font-bold text-slate-800")
                        ui.label("University of Massachusetts Amherst").classes("text-xs font-semibold text-slate-500")
                    ui.label(
                        "RescueLab conducts cutting-edge research in systems, security, and digital forensics. "
                        "RescueBox is developed and maintained as part of our commitment to open-source investigative tools."
                    ).classes("text-slate-600 text-xs leading-relaxed")
                    ui.separator().classes("w-full my-1")
                    ui.link("Visit RescueLab Website", RESCUE_LAB_URL, new_tab=True).classes(
                        "text-sm font-bold text-[#881c1c] hover:underline flex items-center gap-1"
                    )

                # Quick Actions / Resources Card
                with ui.card().classes(
                    "w-full p-6 bg-white border border-slate-200 rounded-2xl shadow-sm border-t-4 border-t-[#881c1c]"
                ):
                    ui.label("Quick Resources").classes("text-sm font-bold text-slate-400 uppercase tracking-wider mb-2")
                    
                    _resources = (
                        ("Case Dashboard", "folder_shared", "/", "Manage active cases and evidence"),
                        ("AI Assistant", "forum", "/chatbot", "Interact with Granite AI models"),
                        ("Jobs & Pipelines", "view_list", "/jobs", "Monitor background tasks"),
                        ("System Logs", "terminal", "/logs", "View real-time application logs"),
                    )
                    
                    with ui.column().classes("w-full gap-2"):
                        for name, icon_name, path, desc in _resources:
                            with ui.row().classes(
                                "w-full p-2.5 rounded-xl border border-slate-100 hover:border-slate-200 hover:bg-slate-50 cursor-pointer items-center gap-3 transition-all"
                            ).on("click", lambda _, p=path: ui.navigate.to(p)):
                                ui.icon(icon_name, size="sm").classes("text-[#881c1c] shrink-0")
                                with ui.column().classes("gap-0.5 flex-1 min-w-0"):
                                    ui.label(name).classes("text-sm font-bold text-slate-800")
                                    ui.label(desc).classes("text-[11px] text-slate-500 truncate")

    logger.debug("About page rendered")
