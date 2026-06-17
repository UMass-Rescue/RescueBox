import os
import sys
import platform
import logging
import threading
import importlib
from pathlib import Path
from typing import Optional
from nicegui import ui, app
from frontend.design_tokens import Design
from frontend.config import DEMO_FOLDERS_BASE, DEMO_FOLDER_NAMES
from .paths import _resolved_existing_directory, _resolved_file_browser_folder
from .storage import get_user_id
from frontend.utils.exceptions import UI_RENDER_ERRORS

logger = logging.getLogger(__name__)


def _get_win32_api_module():
    if sys.platform != "win32":
        return None
    try:
        return importlib.import_module("win32api")
    except ImportError:
        logger.warning(
            "pywin32 is not installed. Windows-specific features are disabled."
        )
        return None


def _add_windows_drives_toggle(container, on_drive_change, current_path):
    win32_api = _get_win32_api_module()
    if platform.system() == "Windows" and win32_api:
        try:
            drives = [d for d in win32_api.GetLogicalDriveStrings().split("\000") if d]
            initial = (
                current_path[0:3]
                if current_path and len(current_path) >= 3 and current_path[1] == ":"
                else drives[0]
            )
            with container:
                ui.toggle(
                    drives,
                    value=initial if initial in drives else None,
                    on_change=lambda e: on_drive_change(e.value),
                ).props(
                    "unelevated color=grey-4 text-color=dark toggle-color=primary toggle-text-color=white"
                ).classes(
                    "w-full mb-2"
                )
        except UI_RENDER_ERRORS:
            pass


_demo_folder_lock = threading.Lock()


_DIR_ROW_ITEM = (
    "w-full items-center justify-between px-3 py-1 hover:bg-zinc-100 rounded-lg "
    "transition-colors group"
)
_DIR_SELECT_BTN = (
    "text-xs opacity-0 group-hover:opacity-100 transition-opacity font-bold "
    "uppercase tracking-wider"
)
_DIR_ROW_NAV = (
    "w-full items-center gap-3 px-3 py-2 cursor-pointer hover:bg-zinc-100 rounded-lg"
)
_FILE_LIST_CLASSES = "w-full flex-1 overflow-y-auto border border-zinc-100 rounded-xl p-2 bg-white min-h-0"
_LOCATION_ROW_CLASSES = (
    "w-full items-center gap-2 p-2 bg-zinc-50 rounded-lg border border-zinc-200"
)


def _set_input_field_value(input_field, value: str) -> None:
    try:
        input_field.set_value(value)
    except UI_RENDER_ERRORS:
        input_field.value = value


def _sorted_directory_entries(p_obj: Path):
    return sorted(p_obj.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))


def _render_parent_directory_row(on_navigate) -> None:
    with ui.row().classes(_DIR_ROW_NAV).on("click", on_navigate):
        ui.icon("arrow_upward", size="sm").classes("text-zinc-500")
        ui.label(".. (Parent Directory)").classes("text-sm font-medium text-zinc-600")


def _render_location_row(current_path: str):
    with ui.row().classes(_LOCATION_ROW_CLASSES):
        ui.label("Location:").classes(
            "text-xs font-bold text-zinc-500 uppercase shrink-0"
        )
        return ui.label(current_path).classes(
            "text-sm font-mono text-zinc-700 break-all"
        )


def _render_tree_access_error(file_list, exc: Exception) -> None:
    logger.error("Error rendering browser tree: %s", exc)
    with file_list:
        ui.label(f"Access denied or error: {exc}").classes("text-xs text-red-500 p-2")


class DirectoryBrowser:
    def __init__(self, on_select, initial_path=None):
        self.on_select = on_select
        self.initial_path = initial_path
        self.state = {"current_path": self._get_start_path()}
        self.dialog = None
        self.path_display = None
        self.file_list = None

    def open(self) -> None:
        """Open the directory picker dialog."""
        self.show()

    def _get_start_path(self) -> str:
        cand = _resolved_existing_directory(self.initial_path)
        if cand:
            return cand
        demo = resolve_demo_folder_for_browser()
        return demo if demo else os.getcwd()

    def _render_directory_tree(self, path):
        self.file_list.clear()
        self.state["current_path"] = path
        try:
            # restrict navigation
            p_obj = Path(path).resolve()
            if not p_obj.exists():
                return

            self.path_display.set_text(str(p_obj))

            with self.file_list:
                if p_obj.parent != p_obj:
                    _render_parent_directory_row(
                        lambda: self._render_directory_tree(str(p_obj.parent))
                    )

                for item in _sorted_directory_entries(p_obj):
                    if item.is_dir():
                        with ui.row().classes(_DIR_ROW_ITEM):
                            # Left side: Navigation
                            with ui.row().classes(
                                "items-center gap-3 cursor-pointer flex-1 py-1"
                            ).on(
                                "click",
                                lambda *a, p=str(item): self._render_directory_tree(p),
                            ):
                                ui.icon("folder", size="sm").classes("text-[#881c1c]")
                                ui.label(item.name).classes(
                                    "text-sm font-medium text-zinc-800"
                                )

                            # Right side: Inline Selection
                            ui.button(
                                "Select",
                                on_click=lambda *a, p=str(item): (
                                    self.on_select(p),
                                    self.dialog.close(),
                                ),
                            ).props("flat dense color=primary").classes(_DIR_SELECT_BTN)
        except UI_RENDER_ERRORS as e:
            _render_tree_access_error(self.file_list, e)

    def show(self):
        # Use PANEL_SHELL_CARD instead of WIDE to avoid clipping on smaller screens
        with ui.dialog() as self.dialog, ui.card().classes(
            Design.PANEL_SHELL_CARD + " h-[80vh] max-h-[800px]"
        ):
            # Header
            with ui.row().classes(Design.PANEL_SHELL_HEADER):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("folder_open", size="md").classes("text-[#881c1c]")
                    ui.label("Select Directory").classes(
                        Design.PANEL_SHELL_HEADER_TITLE
                    )
                ui.button(on_click=self.dialog.close).props("flat round").classes(
                    Design.PANEL_SHELL_HEADER_ICON
                )

            # Body
            with ui.column().classes(Design.PANEL_SHELL_BODY + " gap-3"):
                # Drive selector for Windows
                _add_windows_drives_toggle(
                    ui.column().classes("w-full"),
                    self._render_directory_tree,
                    self.state["current_path"],
                )

                # Path display
                self.path_display = _render_location_row(self.state["current_path"])

                self.file_list = ui.column().classes(_FILE_LIST_CLASSES)
                self._render_directory_tree(self.state["current_path"])

            # Footer
            with ui.row().classes(Design.PANEL_SHELL_FOOTER + " justify-end"):
                ui.button("Cancel", color=None, on_click=self.dialog.close).classes(
                    Design.BTN_MEDIUM_GRAY
                ).props("outline")
                ui.button(
                    "Select This Folder",
                    color=None,
                    on_click=lambda: (
                        self.on_select(self.state["current_path"]),
                        self.dialog.close(),
                    ),
                ).classes(Design.BTN_PRIMARY)

        self.dialog.open()


class FileBrowser:
    def __init__(self, on_select, initial_path=None, filetypes=None):
        self.on_select = on_select
        self.initial_path = initial_path
        self.filetypes = filetypes or []
        self.state = {"current_path": self._get_start_path(), "selected_file": None}
        self.dialog = None
        self.confirm_btn = None
        self.path_display = None
        self.file_list = None
        self.selection_label = None

    def open(self) -> None:
        """Open the file picker dialog."""
        self.show()

    def _get_start_path(self) -> str:
        cand = _resolved_file_browser_folder(self.initial_path)
        if cand:
            return cand
        demo = resolve_demo_folder_for_browser()
        return demo if demo else os.getcwd()

    def _render_file_tree(self, path):
        self.file_list.clear()
        self.state["current_path"] = path
        self.state["selected_file"] = None
        if self.confirm_btn:
            self.confirm_btn.set_visibility(False)

        try:
            p_obj = Path(path).resolve()
            if not p_obj.exists():
                return

            # Update path display
            self.path_display.set_text(str(p_obj))

            with self.file_list:
                if p_obj.parent != p_obj:
                    _render_parent_directory_row(
                        lambda: self._render_file_tree(str(p_obj.parent))
                    )

                entries = _sorted_directory_entries(p_obj)
                dirs = [i for i in entries if i.is_dir()]
                files = [i for i in entries if i.is_file()]

                for item in dirs:
                    with ui.row().classes(_DIR_ROW_NAV).on(
                        "click", lambda *a, p=str(item): self._render_file_tree(p)
                    ):
                        ui.icon("folder", size="sm").classes("text-[#881c1c]")
                        ui.label(item.name).classes("text-sm font-medium text-zinc-800")

                # Render Files
                for item in files:
                    # Filter by filetypes if provided
                    if self.filetypes and not any(
                        item.name.lower().endswith(ft.lower()) for ft in self.filetypes
                    ):
                        continue

                    with ui.row().classes(
                        "w-full items-center gap-3 px-3 py-2 cursor-pointer hover:bg-[#881c1c]/10 rounded-lg group"
                    ).on("click", lambda *a, p=str(item): self._select_file(p)):
                        ui.label(item.name).classes(
                            "text-sm text-zinc-700 group-hover:text-zinc-900"
                        )

        except UI_RENDER_ERRORS as e:
            logger.error("Error rendering file tree: %s", e)

    def _select_file(self, file_path):
        self.state["selected_file"] = file_path
        if self.confirm_btn:
            self.confirm_btn.set_visibility(True)
        # Briefly highlight or show selection?
        # For now just update footer
        self.selection_label.set_text(os.path.basename(file_path))

    def show(self):
        with ui.dialog() as self.dialog, ui.card().classes(
            Design.PANEL_SHELL_CARD + " h-[80vh] max-h-[800px]"
        ):
            # Header
            with ui.row().classes(Design.PANEL_SHELL_HEADER):
                with ui.row().classes("items-center gap-2"):
                    ui.label("Select File").classes(Design.PANEL_SHELL_HEADER_TITLE)
                ui.button(on_click=self.dialog.close).props("flat round").classes(
                    Design.PANEL_SHELL_HEADER_ICON
                )

            # Body
            with ui.column().classes(Design.PANEL_SHELL_BODY + " gap-3"):
                _add_windows_drives_toggle(
                    ui.column().classes("w-full"),
                    self._render_file_tree,
                    self.state["current_path"],
                )

                self.path_display = _render_location_row(self.state["current_path"])

                self.file_list = ui.column().classes(_FILE_LIST_CLASSES)
                self._render_file_tree(self.state["current_path"])

            # Footer
            with ui.row().classes(Design.PANEL_SHELL_FOOTER):
                with ui.row().classes("flex-1 items-center gap-2 overflow-hidden"):
                    ui.label("Selected:").classes(
                        "text-xs font-bold text-zinc-500 uppercase shrink-0"
                    )
                    self.selection_label = ui.label("None").classes(
                        "text-sm font-medium text-[#881c1c] truncate"
                    )

                ui.button("Cancel", color=None, on_click=self.dialog.close).classes(
                    Design.BTN_MEDIUM_GRAY
                ).props("outline")
                self.confirm_btn = ui.button(
                    "Confirm Selection",
                    color=None,
                    on_click=lambda: (
                        self.on_select(self.state["selected_file"]),
                        self.dialog.close(),
                    ),
                ).classes(Design.BTN_PRIMARY)
                self.confirm_btn.set_visibility(False)

        self.dialog.open()


def browse_directory(on_select, initial_path=None):
    DirectoryBrowser(on_select, initial_path).show()


def browse_file(on_select, initial_path=None, filetypes=None):
    FileBrowser(on_select, initial_path, filetypes).show()


def browse_directory_simple(input_field, initial_path=None, on_after_select=None):
    def on_select(path):
        _set_input_field_value(input_field, path)
        if on_after_select:
            on_after_select()

    browse_directory(on_select, initial_path)


def browse_file_simple(
    input_field, initial_path=None, filetypes=None, on_after_select=None
):
    def on_select(path):
        _set_input_field_value(input_field, path)
        if on_after_select:
            on_after_select()

    browse_file(on_select, initial_path, filetypes)


def _user_storage_get(key: str):
    try:
        return app.storage.user.get(key)
    except UI_RENDER_ERRORS:
        return None


def _assign_demo_folder(user_id: str) -> Optional[str]:
    assignments = dict(app.storage.general.get("demo_folder_assignments", {}))
    assigned_paths = set(assignments.values())
    for name in DEMO_FOLDER_NAMES:
        path = str(DEMO_FOLDERS_BASE / user_id / name)
        if path not in assigned_paths:
            assignments[user_id] = path
            app.storage.general["demo_folder_assignments"] = assignments
            app.storage.user["assigned_demo_folder"] = path
            logger.info("Assigned demo folder %s to session %s", path, user_id)
            return path
    logger.warning("No demo folders available for session %s", user_id[:12])
    return None


def get_assigned_demo_folder() -> Optional[str]:
    """
    Get the demo folder assigned to this browser session (Option 1 auto-assign).
    Each session gets one folder from the pool.
    Once assigned, the same folder is returned for this session.
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return None
        existing = _user_storage_get("assigned_demo_folder")
        if existing:
            return existing
        with _demo_folder_lock:
            return _assign_demo_folder(user_id)
    except UI_RENDER_ERRORS as e:
        logger.warning("Error getting assigned demo folder: %s", e)
        return None


def resolve_demo_folder_for_browser() -> Optional[str]:
    """
    Default directory when opening the file/directory browser from plugin forms.
    Uses the session-assigned demo folder when available.
    """
    try:
        assigned = get_assigned_demo_folder()
        if assigned:
            p = Path(assigned)
            if p.is_dir():
                return str(p.resolve())

        base = Path(DEMO_FOLDERS_BASE).expanduser()
        for name in DEMO_FOLDER_NAMES:
            cand = base / name
            if cand.is_dir():
                return str(cand.resolve())
        if base.is_dir():
            return str(base.resolve())
    except UI_RENDER_ERRORS as e:
        logger.debug("resolve_demo_folder_for_browser: %s", e)
    return None


def release_demo_folder_for_client(client) -> None:
    """
    Release the demo folder assigned to this client when it is deleted.
    Call from @app.on_delete with client context.
    """
    try:
        with client:
            user_id = get_user_id()
            if not user_id:
                return
            with _demo_folder_lock:
                assignments = dict(
                    app.storage.general.get("demo_folder_assignments", {})
                )
                if user_id in assignments:
                    released = assignments.pop(user_id)
                    app.storage.general["demo_folder_assignments"] = assignments
                    logger.debug(
                        "Released demo folder %s for deleted session %s",
                        released,
                        user_id[:12],
                    )
    except UI_RENDER_ERRORS as e:
        logger.warning("Error releasing demo folder for client: %s", e)
