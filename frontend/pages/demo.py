"""Demo page - view RescueBox step-by-step guides and sample files."""

import logging
from typing import Optional

from nicegui import ui

from frontend.components.demo import (
    normalize_demo_walkthrough_query,
    render_demo_files_explorer,
)
from frontend.components.demo import schedule_hash_fragment_scroll
from frontend.components.shared import create_navbar
from frontend.constants import NAV_LINKS

logger = logging.getLogger(__name__)

_SAMPLE_FILTER_BLURB: dict[str, str] = {
    "transcribe": "Same top-level folders as the Transcribe walkthrough.",
    "image_search": "Same top-level folders as the Image search walkthrough.",
    "other": "Same top-level folders as the Other plugins walkthrough.",
    "quick_start": "Full demo tree (Quick start).",
}

# Samples-only view: one link back to the in-app guide for this filter.
_WALKTHROUGH_GUIDE_PATH: dict[str, str] = {
    "transcribe": "/demo/transcribe-walkthrough",
    "image_search": "/demo/image-search-walkthrough",
    "other": "/demo/other-walkthrough",
    "quick_start": "/demo/quick-start",
}
_BACK_TO_GUIDE_LABEL: dict[str, str] = {
    "transcribe": "Back to Transcribe walkthrough",
    "image_search": "Back to Search Image walkthrough",
    "other": "Back to Other plugins walkthrough",
    "quick_start": "Back to Quick start",
}


@ui.page("/demo")
async def demo_page(walkthrough: Optional[str] = None):
    """Plain ``/demo`` = full landing. ``?walkthrough=…`` = folders only (matches embedded walkthrough samples)."""
    from frontend.utils import apply_saved_theme

    apply_saved_theme()
    create_navbar()
    from frontend.utils import require_demo_user_session

    if not require_demo_user_session():
        return

    preset = normalize_demo_walkthrough_query(walkthrough)
    samples_only = preset != "all"

    with ui.column().classes(
        "container mx-auto px-4 sm:px-8 py-8 w-full max-w-6xl pb-16"
    ):
        if samples_only:
            with ui.column().props("id=sample-inputs").classes("scroll-mt-24 w-full"):
                with ui.row().classes("items-center gap-2 mb-1"):
                    ui.icon("folder_zip", size="sm").classes("text-[#881c1c]")
                    ui.label("Sample inputs & outputs").classes(
                        "text-2xl font-bold text-slate-800"
                    )
                if preset in _SAMPLE_FILTER_BLURB:
                    ui.label(_SAMPLE_FILTER_BLURB[preset]).classes(
                        "text-zinc-600 text-sm mb-3"
                    )
                guide = _WALKTHROUGH_GUIDE_PATH.get(preset)
                label = _BACK_TO_GUIDE_LABEL.get(preset)
                render_demo_files_explorer(
                    ui.column().classes("w-full min-w-0"), walkthrough=preset
                )
                if guide and label:
                    ui.link(label, guide).classes(
                        "text-[#881c1c] hover:underline text-sm mb-4 inline-block"
                    )

        else:
            with ui.row().classes("items-center gap-2 mb-2"):
                ui.icon("school", size="lg").classes("text-[#881c1c]")
                ui.label("RescueBox Demo").classes("text-4xl font-bold text-slate-800")
            ui.label("Follow the step-by-step guide to learn RescueBox.").classes(
                "text-slate-500 mb-6 pl-1 text-lg"
            )
            with ui.column().classes("gap-3 items-stretch w-full max-w-2xl"):
                # Neutral outline: no Quasar primary / no brand fill (color=None + flat outline).
                _demo_btn = (
                    "text-slate-800 px-6 py-3 rounded-xl font-semibold "
                    "bg-white border border-slate-200 hover:bg-slate-50 hover:shadow-md transition-all "
                    "w-full text-left flex items-center gap-3 border-l-4 border-l-[#881c1c]"
                )
                _demo_btn_props = "flat unelevated no-caps"
                ui.button(
                    "Quick start guide",
                    on_click=lambda: ui.navigate.to("/demo/quick-start"),
                    color=None,
                ).classes(_demo_btn).props(_demo_btn_props)
                ui.button(
                    "1 Plugins menu walkthrough",
                    on_click=lambda: ui.navigate.to("/demo/transcribe-walkthrough"),
                    color=None,
                ).classes(_demo_btn).props(_demo_btn_props)
                ui.button(
                    "2 Chat mode walkthrough",
                    on_click=lambda: ui.navigate.to("/demo/image-search-walkthrough"),
                    color=None,
                ).classes(_demo_btn).props(_demo_btn_props)
                ui.button(
                    "3 Interesting Scenarios walkthrough",
                    on_click=lambda: ui.navigate.to("/demo/other-walkthrough"),
                    color=None,
                ).classes(_demo_btn).props(_demo_btn_props)

            ui.separator().classes("my-8")

            with ui.column().props("id=sample-inputs").classes("scroll-mt-24"):
                ui.label("Sample inputs & outputs").classes("text-2xl font-bold mb-2")
                ui.label("Rescuebox demo folders for each plugin.").classes(
                    "text-zinc-600 mb-4"
                )

                render_demo_files_explorer(
                    ui.column().classes("w-full min-w-0"), walkthrough=preset
                )

            ui.link("Rescuebox Home", NAV_LINKS["home"]).classes(
                "mt-8 text-[#a2aaad] hover:text-[#8a9194] hover:underline"
            )

    schedule_hash_fragment_scroll()
