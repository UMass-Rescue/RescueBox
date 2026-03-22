"""Demo page - view RescueBox step-by-step guides."""

import logging
from nicegui import ui
from frontend.components.shared import create_navbar
from frontend.constants import NAV_LINKS

logger = logging.getLogger(__name__)


@ui.page('/demo')
async def demo_page():
    """Demo page with link to open Quick Start PDF in browser."""
    from frontend.utils.theme import apply_saved_theme
    apply_saved_theme()
    create_navbar()

    with ui.column().classes('container mx-auto p-8'):
        ui.label('RescueBox Demo').classes('text-3xl font-bold mb-4')
        ui.label('Follow the step-by-step guide to learn RescueBox.').classes('text-gray-600 mb-6')
        ui.button(
            'Open Quick Start Guide',
            on_click=lambda: ui.run_javascript(
                'window.open("/demo/RescueBox_Quick_Start.pdf", "_blank")'
            )
        ).classes('bg-blue-600 text-white px-6 py-3')
        ui.link('Back to Home', NAV_LINKS['home']).classes('mt-4 text-blue-600 hover:underline')
