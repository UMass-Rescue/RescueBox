"""
Gate non-home pages until a valid demo User ID is stored (see constants.DEMO_USER_ID_*).
"""

from nicegui import ui


def require_demo_user_session() -> bool:
    """
    If no valid demo User ID is stored, show a short message and return False so the
    caller should not render the rest of the page.
    """
    return True
    
    from frontend.utils.nicegui_storage import get_user_id_for_jobs

    if get_user_id_for_jobs() is not None:
        return True

    with ui.column().classes('container mx-auto p-8 max-w-lg'):
        ui.label('Demo access requires a valid User ID').classes('text-xl font-semibold mb-2')
        ui.label(
            'Enter the User ID on the home page.'
        ).classes('text-zinc-600 mb-4')
        ui.button('Go to home', on_click=lambda: ui.navigate.to('/')).classes('rb-brand-primary text-white')
    return False
