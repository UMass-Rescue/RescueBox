import logging
from nicegui import ui

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def render_file_browser_header(
    title: str = "Select Directory",
    icon: str = "folder_open",
    *,
    light_directory_header: bool = False,
    label_extra_classes: str = "",
) -> None:
    """
    Render a standardized header for file/directory browser dialogs.

    When ``light_directory_header`` is True (directory picker), the bar uses
    UMass Light Gray #a2aaad (see ``.rb-select-directory-header`` in ui_readability_css).

    ``label_extra_classes`` is appended to the title label (optional Tailwind snippets).
    """
    extra = f" {label_extra_classes.strip()}" if label_extra_classes.strip() else ""
    if light_directory_header:
        row_cls = "rb-select-directory-header w-full p-4 items-center"
        icon_cls = "mr-3 shrink-0"
        label_cls = f"text-xl font-semibold text-zinc-900{extra}"
    else:
        row_cls = (
            "bg-gradient-to-r from-[#881c1c] to-[#6a1616] text-white p-4 items-center"
        )
        icon_cls = "mr-3 text-white/80"
        label_cls = f"text-xl font-semibold{extra}"

    with ui.row().classes(row_cls):
        ui.icon(icon, size="2rem").classes(icon_cls)
        ui.label(title).classes(label_cls)
