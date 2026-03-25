"""Demo page - view RescueBox step-by-step guides and sample files."""

import logging
from nicegui import ui
from frontend.components.shared import create_navbar
from frontend.constants import NAV_LINKS

logger = logging.getLogger(__name__)


@ui.page('/demo')
async def demo_page():
    """Demo page with in-app quick start guide and browsable demo inputs/outputs folder."""
    from frontend.utils.theme import apply_saved_theme
    apply_saved_theme()
    create_navbar()

    with ui.column().classes('container mx-auto p-8 max-w-5xl w-full min-w-0'):
        ui.label('RescueBox Demo').classes('text-3xl font-bold mb-4')
        ui.label('Follow the step-by-step guide to learn RescueBox.').classes('text-gray-600 mb-6')
        ui.button(
            'Open quick start guide',
            on_click=lambda: ui.navigate.to('/demo/quick-start'),
        ).classes('bg-blue-600 text-white px-6 py-3')

        ui.separator().classes('my-8')
        ui.label('Sample inputs & outputs').classes('text-2xl font-bold mb-2')
        ui.label(
            'Open folders and files from the demo directory on this machine '
            '(inputs, outputs, and other samples). Files open in the browser when possible.'
        ).classes('text-gray-600 mb-4')

        from frontend.components.demo.demo_files_explorer import render_demo_files_explorer

        render_demo_files_explorer(ui.column().classes('w-full min-w-0'))

        ui.link('Back to Home', NAV_LINKS['home']).classes('mt-8 text-blue-600 hover:underline')
