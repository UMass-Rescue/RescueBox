"""Model list and model card UI components for the plugins page."""

import logging
from typing import List, Dict, Callable, Optional, Any
from datetime import datetime
from nicegui import ui
from frontend.constants import UI_BUTTONS
from frontend.design_tokens import Design
from frontend.components.ui_exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_models_list(
    container: ui.element,
    models: List[Dict[str, Any]],
    server_statuses: Dict[str, str],
    on_inspect: Callable[[str], None],
    on_connect: Callable[[str], None],
) -> None:
    """
    Render a list of model cards into the provided container.
    """
    try:
        with container:
            # Separate online and offline models
            online_models = [
                m for m in models if server_statuses.get(m["uid"]) == "Online"
            ]
            offline_models = [
                m for m in models if server_statuses.get(m["uid"]) != "Online"
            ]

            if online_models:
                # ui.label('Available Models').classes('text-2xl font-bold mt-6 mb-4')
                for model in online_models:
                    render_model_card(
                        container,
                        model,
                        True,
                        on_inspect=lambda uid=model["uid"]: on_inspect(uid),
                        on_connect=None,
                    )

            if offline_models:
                ui.label("Unavailable Models").classes("text-2xl font-bold mt-6 mb-4")
                for model in offline_models:
                    render_model_card(
                        container,
                        model,
                        False,
                        on_inspect=lambda uid=model["uid"]: on_inspect(uid),
                        on_connect=lambda uid=model["uid"]: on_connect(uid),
                    )
    except UI_RENDER_ERRORS as e:
        logger.exception("Failed to render models list: %s", e)
        with container:
            ui.label(f"Error rendering models: {e}").classes("text-red-600")


def render_model_card(
    container,
    model: Dict,
    is_online: bool,
    on_inspect: Optional[Callable] = None,
    on_connect: Optional[Callable] = None,
):
    """
    Render a model card in card-styled row format.
    """
    logger.debug(
        "Rendering model card for model: %s (UID: %s)",
        model.get("name", "Unknown"),
        model.get("uid", "N/A"),
    )
    logger.debug("Model online status: %s", is_online)

    status_indicator = "●" if is_online else "○"
    status_text = "Online" if is_online else "Offline"
    logger.debug("Status indicator: %s, status text: %s", status_indicator, status_text)

    with container:
        logger.debug("Creating model card container")
        with ui.card().classes(
            "rb-models-plugin-card w-full p-6 hover:shadow-md transition-all "
            "border-l-4 border-l-[#881c1c] border-y border-r border-slate-200 "
            "rounded-xl bg-white"
        ):
            with ui.row().classes("items-center justify-between w-full"):
                # Left section - Model info
                with ui.column().classes("flex-1"):
                    # name row
                    with ui.row().classes("items-center gap-3"):
                        ui.label(model["name"]).classes(
                            "text-2xl font-bold text-slate-800"
                        )
                        logger.debug("Model name label added: %s", model["name"])

                    # Version, author, GPU info
                    with ui.row().classes(
                        "gap-4 mt-2 text-sm text-slate-500 items-center"
                    ):
                        ui.label(f"v{model['version']}")
                        ui.label("•")
                        ui.label(model.get("author", "Unknown"))
                        if model.get("gpu"):
                            ui.badge("GPU Required", color="orange").classes(
                                "text-xs font-semibold px-2 py-0.5 rounded"
                            )

                # Right section - Status and actions
                with ui.column().classes("items-end gap-3"):
                    # Status Badge
                    status_pill_cls = (
                        "bg-emerald-50 text-emerald-700 border border-emerald-200"
                        if is_online
                        else "bg-rose-50 text-rose-700 border border-rose-200"
                    )
                    with ui.row().classes(
                        f"items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold {status_pill_cls}"
                    ):
                        ui.icon("check_circle" if is_online else "error", size="14px")
                        ui.label(status_text)

                    # Action buttons
                    with ui.row().classes("gap-2"):
                        logger.debug("Creating action buttons")
                        if on_inspect:
                            ui.button(
                                UI_BUTTONS["plugin_readme"],
                                color=None,
                                on_click=lambda: (
                                    on_inspect(model["uid"]) if on_inspect else None
                                ),
                            ).classes(Design.BTN_PRIMARY_COMPACT)
                            logger.debug("README button added")

                        if not is_online and on_connect:
                            ui.button(
                                "Connect",
                                color=None,
                                on_click=lambda: (
                                    on_connect(model["uid"]) if on_connect else None
                                ),
                            ).classes(
                                "bg-slate-100 hover:bg-slate-200 text-slate-800 px-4 py-2 "
                                "rounded-lg font-medium transition-colors border border-slate-200"
                            )
                            logger.debug("Connect button added (model is offline)")

    logger.debug("Model card rendered successfully")


def render_model_info_card(
    container: ui.element,
    model_info: Any,
    model_info_dict: Dict[str, Any],
    server_status: str,
) -> None:
    """
    Render the right-column model information card used on the model details page
    (metadata and status only; no run action).
    """
    try:
        with container:
            with ui.card().classes(
                "bg-zinc-50 border border-zinc-200 p-6 sticky top-24"
            ):
                ui.label("Plugin").classes("text-xl font-bold mb-4")

                # Version
                with ui.column().classes("gap-2 mb-4"):
                    ui.label("Version").classes("font-semibold")
                    ui.label(
                        model_info.get("version", "")
                        if isinstance(model_info, dict)
                        else getattr(model_info, "version", "")
                    ).classes("text-sm")

                # Author
                with ui.column().classes("gap-2 mb-4"):
                    ui.label("Developed By").classes("font-semibold")
                    ui.label(
                        model_info.get("author", "")
                        if isinstance(model_info, dict)
                        else getattr(model_info, "author", "")
                    ).classes("text-sm")

                # Last Updated
                updated_at = model_info_dict.get("updatedAt")
                cached_at = model_info_dict.get("cached_at")
                updated_str = "N/A"
                if updated_at:
                    try:
                        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                        updated_str = dt.strftime("%Y-%m-%d %H:%M:%S EDT")
                    except UI_RENDER_ERRORS:
                        updated_str = str(updated_at)
                elif cached_at:
                    try:
                        dt = datetime.fromisoformat(cached_at)
                        updated_str = dt.strftime("%Y-%m-%d %H:%M:%S EDT")
                    except UI_RENDER_ERRORS:
                        updated_str = "N/A"

                with ui.column().classes("gap-2 mb-4"):
                    ui.label("Last Updated").classes("font-semibold")
                    ui.label(updated_str).classes("text-sm")

                # Server Status
                with ui.column().classes("gap-2 mb-4"):
                    ui.label("Status").classes("font-semibold")
                    status_color = (
                        "text-green-600"
                        if server_status == "Online"
                        else "text-red-600"
                    )
                    ui.label(server_status).classes(
                        f"text-sm font-semibold {status_color}"
                    )

                # GPU info
                gpu_required = (
                    model_info.gpu
                    if model_info and hasattr(model_info, "gpu")
                    else model_info_dict.get("gpu", False)
                )
                if gpu_required:
                    with ui.column().classes("gap-2 mb-4"):
                        ui.badge("GPU Required", color="red").classes("text-xs")
    except UI_RENDER_ERRORS as e:
        logger.exception("Error rendering model info card: %s", e)
        with container:
            ui.label(f"Error rendering model info: {e}").classes("text-red-600")
