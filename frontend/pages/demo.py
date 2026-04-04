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
        ui.label('Follow the step-by-step guide to learn RescueBox.').classes('text-black-600 mb-6')
        with ui.column().classes('gap-3 items-start'):
            ui.button(
                'Quick start guide',
                on_click=lambda: ui.navigate.to('/demo/quick-start'),
            ).classes('bg-blue-600 text-white px-6 py-3')
            ui.button(
                'Plugins menu walkthrough 1',
                on_click=lambda: ui.navigate.to('/demo/transcribe-walkthrough'),
            ).classes('bg-green-600 text-white px-6 py-3')
            ui.button(
                'Chat mode walkthrough 2',
                on_click=lambda: ui.navigate.to('/demo/image-search-walkthrough'),
            ).classes('bg-violet-600 text-white px-6 py-3')
            ui.button(
                'Interesting Scenarios walkthrough 3',
                on_click=lambda: ui.navigate.to('/demo/other-walkthrough'),
            ).classes('bg-amber-600 text-white px-6 py-3')

        ui.separator().classes('my-8')

        # with ui.column().props('id=sample-inputs').classes('scroll-mt-24'):
        #     ui.label('Sample inputs & outputs').classes('text-2xl font-bold mb-2')
        #     ui.label(
        #         'Review inputs and outputs used in the walkthroughs. '
        #         'You can link directly to this section.'
        #     ).classes('text-black-600 mb-4')

        #     from frontend.components.demo.demo_files_explorer import render_demo_files_explorer

        #     render_demo_files_explorer(ui.column().classes('w-full min-w-0'), walkthrough='all')

        # ui.link('Rescuebox Home', NAV_LINKS['home']).classes('mt-8 text-blue-600 hover:underline')
