import os
import sys
import platform
import logging
import threading
from pathlib import Path
from typing import Optional
from nicegui import ui, app
from frontend.design_tokens import Design
from frontend.config import DEMO_FOLDERS_BASE, DEMO_FOLDER_NAMES
from .paths import _resolved_existing_directory, _resolved_file_browser_folder

logger = logging.getLogger(__name__)

if sys.platform == "win32":
    try:
        import win32api  # pyright: ignore[reportMissingModuleSource]
    except ImportError:
        win32api = None
        logger.warning(
            "pywin32 is not installed. Windows-specific features are disabled."
        )
else:
    # Safely mock it out for Linux/Mac
    win32api = None


_demo_folder_lock = threading.Lock()


def _add_windows_drives_toggle(container, on_drive_change, current_path):
    if platform.system() == "Windows" and win32api:
        try:
            drives = [d for d in win32api.GetLogicalDriveStrings().split("\000") if d]
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
        except Exception:
            pass


class DirectoryBrowser:
    def __init__(self, on_select, initial_path=None):
        self.on_select = on_select
        self.initial_path = initial_path
        self.state = {"current_path": self._get_start_path()}
        self.dialog = None

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
            from .storage import get_user_id

            user_id = get_user_id()
            user_root = (DEMO_FOLDERS_BASE / user_id).resolve()

            # Optional: If this is their first time doing anything, ensure their folder exists
            if not user_root.exists():
                user_root.mkdir(parents=True, exist_ok=True)
            safe_relative_input = str(path).lstrip("/\\")

            # 3. Combine and mathematically collapse the path

            requested_path = (user_root / safe_relative_input).resolve()
            # Update path display
            if not requested_path.absolute().is_relative_to(user_root.absolute()):
                logger.error(
                    "Error is_relative_to: %s %s",
                    requested_path.absolute(),
                    user_root.absolute(),
                )
                # raise PermissionError(f"Security Violation: Path traversal blocked for user {user_id}")

            # 5. Check if it actually exists before returning
            if not requested_path.exists():
                logger.error("Error requested_path: %s does not exist", requested_path)
                # raise FileNotFoundError(f"The path '{str(p_obj)}' does not exist.")
            self.path_display.set_text(str(p_obj))

            with self.file_list:
                # Parent directory option
                if p_obj.parent != p_obj:
                    with ui.row().classes(
                        "w-full items-center gap-3 px-3 py-2 cursor-pointer hover:bg-zinc-100 rounded-lg transition-colors"
                    ).on(
                        "click", lambda: self._render_directory_tree(str(p_obj.parent))
                    ):
                        ui.icon("arrow_upward", size="sm").classes("text-zinc-500")
                        ui.label(".. (Parent Directory)").classes(
                            "text-sm font-medium text-zinc-600"
                        )

                # Subdirectories
                items = sorted(
                    p_obj.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())
                )
                for item in items:
                    if item.is_dir():
                        with ui.row().classes(
                            "w-full items-center justify-between px-3 py-1 hover:bg-zinc-100 rounded-lg transition-colors group"
                        ):
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
                            ).props("flat dense color=primary").classes(
                                "text-xs opacity-0 group-hover:opacity-100 transition-opacity font-bold uppercase tracking-wider"
                            )
        except Exception as e:
            logger.error("Error rendering directory tree: %s", e)
            with self.file_list:
                ui.label(f"Access denied or error: {str(e)}").classes(
                    "text-xs text-red-500 p-2"
                )

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
                ui.button(icon="close", on_click=self.dialog.close).props(
                    "flat round"
                ).classes(Design.PANEL_SHELL_HEADER_ICON)

            # Body
            with ui.column().classes(Design.PANEL_SHELL_BODY + " gap-3"):
                # Drive selector for Windows
                _add_windows_drives_toggle(
                    ui.column().classes("w-full"),
                    self._render_directory_tree,
                    self.state["current_path"],
                )

                # Path display
                with ui.row().classes(
                    "w-full items-center gap-2 p-2 bg-zinc-50 rounded-lg border border-zinc-200"
                ):
                    ui.label("Location:").classes(
                        "text-xs font-bold text-zinc-500 uppercase shrink-0"
                    )
                    self.path_display = ui.label(self.state["current_path"]).classes(
                        "text-sm font-mono text-zinc-700 break-all"
                    )

                # Directory list - use flex-1 to fill available body space
                self.file_list = ui.column().classes(
                    "w-full flex-1 overflow-y-auto border border-zinc-100 rounded-xl p-2 bg-white min-h-0"
                )
                self._render_directory_tree(self.state["current_path"])

            # Footer
            with ui.row().classes(Design.PANEL_SHELL_FOOTER + " justify-end"):
                ui.button("Cancel", on_click=self.dialog.close).classes(
                    Design.BTN_MEDIUM_GRAY
                ).props("outline")
                ui.button(
                    "Select This Folder",
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
                # Parent directory
                if p_obj.parent != p_obj:
                    with ui.row().classes(
                        "w-full items-center gap-3 px-3 py-2 cursor-pointer hover:bg-zinc-100 rounded-lg"
                    ).on("click", lambda: self._render_file_tree(str(p_obj.parent))):
                        ui.icon("arrow_upward", size="sm").classes("text-zinc-500")
                        ui.label(".. (Parent Directory)").classes(
                            "text-sm font-medium text-zinc-600"
                        )

                items = sorted(
                    p_obj.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())
                )

                # Split into dirs and files
                dirs = [i for i in items if i.is_dir()]
                files = [i for i in items if i.is_file()]

                # Render Directories
                for item in dirs:
                    with ui.row().classes(
                        "w-full items-center gap-3 px-3 py-2 cursor-pointer hover:bg-zinc-100 rounded-lg"
                    ).on("click", lambda *a, p=str(item): self._render_file_tree(p)):
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
                        ui.icon("insert_drive_file", size="sm").classes(
                            "text-zinc-400 group-hover:text-[#881c1c]"
                        )
                        ui.label(item.name).classes(
                            "text-sm text-zinc-700 group-hover:text-zinc-900"
                        )

        except Exception as e:
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
                    ui.icon("insert_drive_file", size="md").classes("text-[#881c1c]")
                    ui.label("Select File").classes(Design.PANEL_SHELL_HEADER_TITLE)
                ui.button(icon="close", on_click=self.dialog.close).props(
                    "flat round"
                ).classes(Design.PANEL_SHELL_HEADER_ICON)

            # Body
            with ui.column().classes(Design.PANEL_SHELL_BODY + " gap-3"):
                _add_windows_drives_toggle(
                    ui.column().classes("w-full"),
                    self._render_file_tree,
                    self.state["current_path"],
                )

                with ui.row().classes(
                    "w-full items-center gap-2 p-2 bg-zinc-50 rounded-lg border border-zinc-200"
                ):
                    ui.label("Location:").classes(
                        "text-xs font-bold text-zinc-500 uppercase shrink-0"
                    )
                    self.path_display = ui.label(self.state["current_path"]).classes(
                        "text-sm font-mono text-zinc-700 break-all"
                    )

                self.file_list = ui.column().classes(
                    "w-full flex-1 overflow-y-auto border border-zinc-100 rounded-xl p-2 bg-white min-h-0"
                )
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

                ui.button("Cancel", on_click=self.dialog.close).classes(
                    Design.BTN_MEDIUM_GRAY
                ).props("outline")
                self.confirm_btn = ui.button(
                    "Confirm Selection",
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
        try:
            input_field.set_value(path)
        except Exception:
            input_field.value = path
        if on_after_select:
            on_after_select()

    browse_directory(on_select, initial_path)


def browse_file_simple(
    input_field, initial_path=None, filetypes=None, on_after_select=None
):
    def on_select(path):
        try:
            input_field.set_value(path)
        except Exception:
            input_field.value = path
        if on_after_select:
            on_after_select()

    browse_file(on_select, initial_path, filetypes)


def get_assigned_demo_folder() -> Optional[str]:
    """
    Get the demo folder assigned to this browser session (Option 1 auto-assign).
    Each session gets one folder from the pool.
    Once assigned, the same folder is returned for this session.
    """
    try:
        from .storage import get_user_id

        user_id = get_user_id()
        if not user_id:
            return None
        # Check if this session already has an assignment
        try:
            existing = app.storage.user.get("assigned_demo_folder")
            if existing:
                return existing
        except Exception:
            pass
        # Assign next available folder
        with _demo_folder_lock:
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
    except Exception as e:
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
    except Exception as e:
        logger.debug("resolve_demo_folder_for_browser: %s", e)
    return None


def release_demo_folder_for_client(client) -> None:
    """
    Release the demo folder assigned to this client when it is deleted.
    Call from @app.on_delete with client context.
    """
    try:
        from .storage import get_user_id

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
    except Exception as e:
        logger.warning("Error releasing demo folder for client: %s", e)
