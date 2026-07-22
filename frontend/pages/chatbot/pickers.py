"""Tool and analysis picker UI (no dependency on coordinator or ui page)."""

from __future__ import annotations

import logging

from nicegui import ui

from frontend.chatbot.config import ToolRegistry
from frontend.design_tokens import Design

logger = logging.getLogger(__name__)


_TOOL_ICON_BOX = (
    "w-12 h-12 rounded-xl bg-[#881c1c]/5 flex items-center justify-center "
    "shrink-0 border border-[#881c1c]/10"
)
_TOOL_DESC = (
    "text-sm sm:text-base text-slate-500 whitespace-normal break-words leading-relaxed"
)
_LAUNCH_ROW = (
    "items-center gap-1 shrink-0 text-[#881c1c] font-semibold text-sm "
    "bg-[#881c1c]/5 hover:bg-[#881c1c]/10 px-3 py-1.5 rounded-lg transition-all"
)


class ToolPicker:
    def __init__(self, container, tool_registry, on_tool_selected):
        self.container = container
        self.tool_registry = tool_registry
        self.on_tool_selected = on_tool_selected
        self.logger = logging.getLogger(self.__class__.__name__)

    def menu_registry(self):
        """Tool registry backing this picker."""
        return self.tool_registry

    async def show(self):
        self.logger.debug(
            "ToolPicker.show started. Registry type: %s", type(self.tool_registry)
        )

        menu = getattr(self.tool_registry, "TOOL_MENU", {})
        if not menu:
            menu = ToolRegistry.TOOL_MENU

        self.logger.info(
            "ToolPicker.show menu source: %s. Items: %d",
            "Instance" if hasattr(self.tool_registry, "TOOL_MENU") else "Class",
            len(menu),
        )

        with self.container:
            with ui.card().classes(
                "w-full max-w-full bg-white border border-slate-200 shadow-md rounded-2xl overflow-hidden p-0"
            ):
                with ui.column().classes("p-6 gap-3 w-full bg-slate-50"):
                    ui.label("Choose a plugin to run:").classes(
                        "text-sm font-semibold text-slate-500 uppercase tracking-wider"
                    )
                    if not menu:
                        ui.label("No plugins available in TOOL_MENU.").classes(
                            "text-sm text-rose-500 font-medium"
                        )
                    else:
                        for num, tool in menu.items():
                            self.logger.debug(
                                "Adding tool to UI: %s - %s",
                                num,
                                tool.get("name"),
                            )
                            row = ui.row().classes(
                                "w-full min-w-0 py-4 px-5 rounded-xl border border-slate-200 bg-white shadow-sm "
                                "hover:bg-slate-50 hover:border-[#881c1c] cursor-pointer transition-all duration-150 "
                                "items-center justify-between gap-4 border-l-4 border-l-[#881c1c]"
                            )
                            row.on(
                                "click",
                                lambda *a, t=tool: self.on_tool_selected(
                                    t["endpoint"], {}
                                ),
                            )
                            with row:
                                with ui.row().classes(
                                    "items-center gap-4 flex-1 min-w-0"
                                ):

                                    with ui.column().classes("flex-1 min-w-0 gap-0.5"):
                                        ui.label(f'{num}. {tool["name"]}').classes(
                                            "text-lg font-bold text-slate-800 leading-snug"
                                        )
                                        ui.label(
                                            tool.get("desc", "No description")
                                        ).classes(_TOOL_DESC)

                                with ui.row().classes(_LAUNCH_ROW):
                                    ui.label("Run")

        self.logger.info("ToolPicker.show finished building UI.")


class AnalysisPicker:
    def __init__(self, container, on_analysis_selected):
        self.container = container
        self.on_analysis_selected = on_analysis_selected
        self.logger = logging.getLogger(self.__class__.__name__)

    def target_container(self):
        """UI container where analysis options are rendered."""
        return self.container

    async def show(self):
        self.logger.info("AnalysisPicker.show started")
        with self.container:
            with ui.card().classes(
                "w-full max-w-full bg-white border border-slate-200 shadow-md rounded-2xl overflow-hidden p-0"
            ):
                with ui.row().classes(Design.PANEL_SHELL_HEADER):
                    with ui.row().classes("items-center gap-2"):
                        ui.label("Analysis Mode").classes(
                            Design.PANEL_SHELL_HEADER_TITLE
                        )

                with ui.column().classes("p-6 gap-3 w-full bg-slate-50"):
                    ui.label("Select an analysis type:").classes(
                        "text-sm font-semibold text-slate-500 uppercase tracking-wider"
                    )
                    options = ["Surface Scan", "Deep Forensic", "AI Content Analysis"]
                    analysis_details = {
                        "Surface Scan": {
                            "desc": "Quickly analyze metadata, file headers, and basic structures",
                            "icon": "radar",
                        },
                        "Deep Forensic": {
                            "desc": "Comprehensive, byte-level analysis of all partitions and hidden data",
                            "icon": "biotech",
                        },
                        "AI Content Analysis": {
                            "desc": "Leverage machine learning models to detect objects, faces, and transcribe media",
                            "icon": "psychology",
                        },
                    }
                    for a_type in options:
                        details = analysis_details.get(
                            a_type,
                            {"desc": "Run automated analysis", "icon": "analytics"},
                        )
                        self.logger.info("Adding analysis option: %s", a_type)
                        row = ui.row().classes(
                            "w-full min-w-0 py-4 px-5 rounded-xl border border-slate-200 bg-white shadow-sm "
                            "hover:bg-slate-50 hover:border-[#881c1c] cursor-pointer transition-all duration-150 "
                            "items-center justify-between gap-4 border-l-4 border-l-[#881c1c]"
                        )
                        row.on(
                            "click", lambda *a, t=a_type: self.on_analysis_selected(t)
                        )
                        with row:
                            with ui.row().classes("items-center gap-4 flex-1 min-w-0"):
                                with ui.element("div").classes(_TOOL_ICON_BOX):
                                    ui.icon(details["icon"], size="24px").classes(
                                        "text-[#881c1c]"
                                    )

                                with ui.column().classes("flex-1 min-w-0 gap-0.5"):
                                    ui.label(a_type).classes(
                                        "text-lg font-bold text-slate-800 leading-snug"
                                    )
                                    ui.label(details["desc"]).classes(_TOOL_DESC)

                            with ui.row().classes(_LAUNCH_ROW):
                                ui.label("Analyze")
                                ui.icon("arrow_forward", size="16px")
        self.logger.debug("AnalysisPicker.show finished building UI.")
