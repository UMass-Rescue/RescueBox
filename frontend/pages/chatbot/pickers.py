"""
Chatbot Pickers

This module contains picker classes for tool selection and analysis type selection.
"""

import logging
from nicegui import ui
from typing import Callable
from frontend.pages.chatbot.utils.ui_operations import UIOperations
from frontend.chatbot.config import ToolRegistry
from frontend.pages.chatbot.constants import FormConfig
from frontend.design_tokens import Design

logger = logging.getLogger(__name__)


class BasePicker:
    """Base class for picker dialogs with common functionality."""

    def __init__(self, container: ui.element, title: str, card_classes: str):
        self.container = container
        self.title = title
        self.card_classes = card_classes
        self.picker_card = None
        self.input_field = None

    def create_picker_card(self) -> ui.card:
        """Create the main picker card container."""
        self.picker_card = ui.card().classes(self.card_classes)
        return self.picker_card

    def create_header(self, color: str = 'indigo'):
        """Create the picker header with title (no emoji)."""
        with ui.column().classes('p-3 space-y-2'):
            ui.label(self.title).classes(
                f'text-lg font-bold text-{color}-900 tracking-tight'
            )

    def create_submit_button(self, text: str, color: str, on_click):
        """Create the submit button."""
        ui.button(text, on_click=on_click).classes(f'bg-{color}-600 text-white mt-2')

    def show_loading_indicator(self, message: str, color: str):
        """Show a loading indicator in the container."""

        UIOperations.scroll_to_bottom()
        with self.container:
            loading_row = ui.row().classes('justify-center py-4')
            with loading_row:
                ui.spinner(size='2rem').classes(f'text-{color}-600')
                ui.label(message).classes(f'ml-2 text-{color}-700')
            return loading_row

    def cleanup_and_load(self, on_selected_callback):
        """Clean up picker and trigger the selected callback."""
        self.picker_card.delete()
        return on_selected_callback()


class ToolPicker(BasePicker):
    """Picker for selecting tools from the tool registry."""

    def __init__(self, container: ui.element, tool_registry: ToolRegistry,
                 on_tool_selected: Callable[[str, dict], None]):
        super().__init__(container, 'RescueBox Plugin Selector', FormConfig.TOOL_PICKER_CLASSES)
        self.tool_registry = tool_registry
        self.on_tool_selected = on_tool_selected

    async def show(self):
        """Show the tool picker dialog."""
        logger.info("Showing tool picker menu")
        try:
            from frontend.components.pickers.tool_picker_dialog import show_tool_picker_dialog

            with self.container:
                show_tool_picker_dialog(
                    ui.column(), self.tool_registry, self.on_tool_selected
                )
            logger.debug("Tool picker menu displayed (via component)")
        except Exception:
            logger.exception("Failed to render tool picker via component, falling back to inline")
            from frontend.components.pickers.tool_picker_dialog import show_tool_picker_dialog

            with self.container:
                show_tool_picker_dialog(
                    ui.column(), self.tool_registry, self.on_tool_selected
                )

            logger.debug("Tool picker menu displayed")

    def _create_tool_buttons(self):
        """Create clickable tool buttons."""
        ui.label('Available Tools').classes('text-xl font-bold text-zinc-800 tracking-tight')
        ui.label('Click a tool to use').classes('text-base text-zinc-600 mb-4')
        with ui.column().classes('gap-2 w-full'):
            for num, tool in self.tool_registry.TOOL_MENU.items():
                row = ui.row().classes(
                    f"w-full min-w-0 py-5 px-5 rounded-xl {Design.CHATBOT_PLUGIN_MENU_ROW}"
                )
                row.on('click', lambda *a, n=num: self._handle_tool_click(n))
                with row:
                    ui.label(f'{num}. {tool["name"]} — {tool["desc"]}').classes(
                        'w-full text-left text-sm leading-snug font-medium text-zinc-900 '
                        'whitespace-normal break-words'
                    )

    def _handle_tool_click(self, num: str):
        """Load the tool form when user clicks a tool button."""
        if num not in self.tool_registry.TOOL_MENU:
            return
        tool = self.tool_registry.TOOL_MENU[num]
        import asyncio

        async def load():
            loading = self.show_loading_indicator('Loading form...', 'indigo')
            try:
                await self.on_tool_selected(tool['endpoint'], {})
            finally:
                loading.delete()

        asyncio.create_task(load())


class AnalysisPicker(BasePicker):
    """Picker for selecting analysis types."""

    def __init__(self, container: ui.element, on_analysis_selected: Callable[[str], None]):
        super().__init__(container, 'Analysis Type Picker', FormConfig.ANALYSIS_PICKER_CLASSES)
        self.on_analysis_selected = on_analysis_selected

    async def show(self):
        """Show the analysis picker dialog."""
        logger.info("Showing analysis picker menu")
        try:
            from frontend.components.pickers.analysis_picker_dialog import show_analysis_picker_dialog
            with self.container:
                with self.create_picker_card():
                    self.create_header('indigo')
                    with ui.row().classes('gap-4 w-full'):
                        show_analysis_picker_dialog(ui.column(), FormConfig.ANALYSIS_OPTIONS, lambda name: self.on_analysis_selected(name))
                        with ui.card().classes('bg-white p-4 flex-1'):
                            self._create_input_form()
            logger.debug("Analysis picker menu displayed (via component)")
        except Exception:
            logger.exception("Failed to render analysis picker via component, falling back to inline")
            with self.container:
                with self.create_picker_card():
                    self.create_header('indigo')
                    
                    with ui.row().classes('gap-4 w-full'):
                        with ui.card().classes('bg-white p-4 flex-1'):
                            self._create_analysis_buttons()
                        with ui.card().classes('bg-white p-4 flex-1'):
                            self._create_input_form()

            logger.debug("Analysis picker menu displayed")

    def _create_analysis_buttons(self):
        """Create clickable analysis option buttons on the left side."""
        ui.label('Choose what you want to analyze:').classes('font-semibold mb-3')
        with ui.column().classes('gap-2'):
            for num, option in FormConfig.ANALYSIS_OPTIONS.items():
                ui.button(
                    f'{num}. {option["name"]} - {option["desc"]}',
                    on_click=lambda n=num: self._handle_selection(n)
                ).classes('text-left p-2 h-auto whitespace-normal justify-start text-sm bg-zinc-100 text-zinc-800 border border-zinc-200 hover:bg-zinc-200')

    def _handle_selection(self, num: int):
        """Handle the visual selection of an analysis option."""
        self.input_field.set_value(str(num))
        ui.notify(f'Selected option {num}', type='info', classes='rb-notify-505759')

    def _create_input_form(self):
        """Create the input form on the right side."""
        ui.label('Choose an option:').classes('font-semibold mb-2')
        self.input_field = ui.input(label='Choose an option:', placeholder='Option Number (1-5)').classes('w-full')

        async def on_submit():
            try:
                choice_num = int(self.input_field.value.strip())
                if choice_num in FormConfig.ANALYSIS_OPTIONS:
                    analysis_type = FormConfig.ANALYSIS_OPTIONS[choice_num]['name']

                    loading_indicator = self.show_loading_indicator('Starting analysis...', 'indigo')
                    try:
                        await self.on_analysis_selected(analysis_type)
                    finally:
                        loading_indicator.delete()
                else:
                    max_val = len(FormConfig.ANALYSIS_OPTIONS)
                    ui.notify(f'Invalid choice. Please enter 1-{max_val}.', type='negative', classes='rb-notify-505759')
            except ValueError:
                ui.notify('Please enter a valid number.', type='negative', classes='rb-notify-505759')

        self.create_submit_button('Start Analysis', 'green', on_submit)
