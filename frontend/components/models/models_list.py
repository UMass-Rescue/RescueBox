import logging
from nicegui import ui
from typing import List, Dict, Callable, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_models_list(container: ui.element, models: List[Dict[str, Any]], server_statuses: Dict[str, str], on_inspect: Callable[[str], None], on_connect: Callable[[str], None]) -> None:
    """
    Render a list of model cards into the provided container.
    """
    try:
        with container:
            # Separate online and offline models
            online_models = [m for m in models if server_statuses.get(m['uid']) == 'Online']
            offline_models = [m for m in models if server_statuses.get(m['uid']) != 'Online']

            if online_models:
                # ui.label('Available Models').classes('text-2xl font-bold mt-6 mb-4')
                for model in online_models:
                    from frontend.components.models.model_card import render_model_card
                    render_model_card(
                        container,
                        model,
                        True,
                        on_inspect=lambda uid=model['uid']: on_inspect(uid),
                        on_connect=None
                    )

            if offline_models:
                ui.label('Unavailable Models').classes('text-2xl font-bold mt-6 mb-4')
                for model in offline_models:
                    from frontend.components.models.model_card import render_model_card
                    render_model_card(
                        container,
                        model,
                        False,
                        on_inspect=lambda uid=model['uid']: on_inspect(uid),
                        on_connect=lambda uid=model['uid']: on_connect(uid)
                    )
    except Exception as e:
        logger.exception("Failed to render models list: %s", e)
        with container:
            ui.label(f'Error rendering models: {e}').classes('text-red-600')

