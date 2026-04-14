"""
File and Directory Browser Utilities

This module provides cross-platform file and directory browser dialogs using
NiceGUI components. It includes Windows-specific drive selection and uses
Pydantic models for path validation.
"""

import logging
from nicegui import ui
from typing import Optional, Callable
import os
import platform
from pathlib import Path
from rb.api.models import DirectoryInput, FileInput
from pydantic import ValidationError

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _resolved_existing_directory(initial: Optional[str]) -> Optional[str]:
    """Return resolved path if *initial* is an existing directory, else None."""
    if initial is None:
        return None
    s = str(initial).strip()
    if not s:
        return None
    try:
        p = Path(s).expanduser()
        if not p.is_absolute():
            p = Path(os.getcwd()) / p
        rp = p.resolve()
        if rp.is_dir():
            return str(rp)
    except OSError:
        pass
    return None


def _resolved_file_browser_folder(initial: Optional[str]) -> Optional[str]:
    """Folder to show in the file browser: existing dir, or parent of an existing file."""
    if initial is None:
        return None
    s = str(initial).strip()
    if not s:
        return None
    try:
        p = Path(s).expanduser()
        if not p.is_absolute():
            p = Path(os.getcwd()) / p
        rp = p.resolve()
        if rp.is_dir():
            return str(rp)
        if rp.is_file():
            return str(rp.parent.resolve())
    except OSError:
        pass
    return None


def _add_windows_drives_toggle(container, on_drive_change: Callable[[str], None], current_path: str):
    """
    Add Windows drive toggle if running on Windows.
    
    Creates a toggle widget for selecting Windows drives (C:/, D:/, etc.)
    when running on Windows. Uses win32api to detect available drives.
    
    Args:
        container: NiceGUI container to add toggle to
        on_drive_change (Callable[[str], None]): Callback function called when drive is changed.
            Receives the selected drive path (e.g., 'C:\\')
        current_path (str): Current path to determine initial drive selection
    
    Returns:
        Optional[ui.toggle]: Toggle widget if created, None otherwise
    
    Tips:
    - Only works on Windows platform
    - Requires win32api module (pywin32 package)
    - Gracefully handles missing win32api import
    - Initial drive is determined from current_path or defaults to first available drive
    """
    logger.debug("Checking for Windows drive toggle")
    if platform.system() == 'Windows':
        logger.debug("Windows platform detected, creating drive toggle")
        try:
            import win32api
            drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
            # Remove any empty entries and normalize list
            drives = [d for d in drives if d]
            logger.debug("Found %d Windows drives: %s", len(drives), drives)

            # Determine initial drive from current path if valid, otherwise default to first available
            if current_path and len(current_path) >= 3 and current_path[1] == ':':
                initial_drive = current_path[0:3]
            else:
                initial_drive = drives[0] if drives else None

            # Ensure initial_drive is one of the available drives
            if initial_drive not in drives:
                logger.debug("Requested initial drive %s not in available drives, falling back", initial_drive)
                initial_drive = drives[0] if drives else None

            logger.debug("Initial drive selected: %s", initial_drive)

            with container:
                try:
                    if initial_drive is not None:
                        drives_toggle = ui.toggle(
                            drives,
                            value=initial_drive,
                            on_change=lambda e: on_drive_change(e.value)
                        ).classes('w-full mb-2')
                    else:
                        drives_toggle = ui.toggle(
                            drives,
                            on_change=lambda e: on_drive_change(e.value)
                        ).classes('w-full mb-2')
                    logger.info("Windows drive toggle created successfully")
                    return drives_toggle
                except (ValueError, TypeError) as e:
                    # Toggle may reject values; try fallback to select
                    logger.warning("Error creating drive toggle widget: %s, falling back to select", str(e))
                    try:
                        from frontend.utils.nicegui_compat import select as safe_select
                        select = safe_select(drives, value=initial_drive if initial_drive in drives else None,
                                            on_change=lambda e: on_drive_change(e.value))  # type: ignore[call-arg]
                        select.classes('w-full mb-2')
                        return select
                    except (ValueError, TypeError) as e2:
                        logger.warning("Error creating fallback select for drives: %s", str(e2))
                        return None
        except ImportError:
            logger.debug("win32api not available, skipping drive toggle")
            # win32api not available, skip drive toggle
        except OSError as e:
            logger.warning("Error getting Windows drives: %s, skipping drive toggle", str(e))
            # Error getting drives, skip drive toggle
    return None


class DirectoryBrowser:
    """Refactored directory browser with clean separation of concerns."""

    def __init__(self, on_select: Callable[[str], None], initial_path: Optional[str] = None):
        self.on_select = on_select
        self.initial_path = initial_path
        self.state = {'current_path': self._get_start_path()}
        self.dialog = None
        self.path_input = None
        self.file_list = None
        self.drive_container = None

    def _get_start_path(self) -> str:
        """Prefer an existing *initial_path*; else demo folder; else cwd."""
        cand = _resolved_existing_directory(self.initial_path)
        if cand:
            return cand
        try:
            from frontend.utils.nicegui_storage import resolve_demo_folder_for_browser
            demo = resolve_demo_folder_for_browser()
            if demo:
                return demo
        except Exception as e:
            logger.debug("Could not resolve demo folder for browser: %s", e)
        return os.getcwd()

    def _create_dialog_header(self):
        """Create the dialog header with title."""
        try:
            from frontend.components.file_browser.header import render_file_browser_header
            render_file_browser_header("Select Directory", icon='folder_open')
        except (ImportError, ModuleNotFoundError):
            with ui.row().classes('bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 items-center'):
                ui.icon('folder_open', size='2rem').classes('mr-3')
                ui.label('Select Directory').classes('text-xl font-semibold')

    def _jump_to_path(self, raw: str) -> None:
        """Navigate to an absolute or user-relative path (e.g. UFDR mount under /tmp)."""
        s = (raw or "").strip()
        if not s:
            ui.notify("Enter a folder path", type="warning")
            return
        try:
            p = Path(s).expanduser()
            if not p.is_absolute():
                p = Path(os.getcwd()) / p
            rp = str(p.resolve())
            if not os.path.isdir(rp):
                ui.notify(f"Not a directory or not accessible: {rp}", type="negative")
                return
            self._render_directory_tree(rp)
        except OSError as e:
            ui.notify(f"Invalid path: {e}", type="negative")

    def _create_navigation_bar(self):
        """Create the navigation bar with address bar and buttons."""
        with ui.row().classes('bg-gray-50 border-b p-3 items-center gap-2'):
            ui.icon('home', size='1.2rem').classes('text-gray-500')
            try:
                self.full_path_label = ui.label(self.state['current_path']).classes('text-xs font-mono text-gray-600 mt-1 break-words')
                self.full_path_label.bind_text_from(self.state, 'current_path')
            except Exception:
                # binding may not be available in test environments; best-effort only
                pass
        with ui.row().classes('bg-gray-50 border-b px-3 pb-3 pt-0 items-center gap-2 flex-wrap'):
            jump = ui.input(
                placeholder="Paste folder path (e.g. /tmp/case123/files/Image) — Enter or Go",
                value=self.state["current_path"],
            ).classes("flex-1 min-w-[12rem]").props("outlined dense")
            self._path_jump_input = jump
            ui.button("Go", on_click=lambda: self._jump_to_path(jump.value)).classes("shrink-0")
            try:
                jump.on("keydown.enter", lambda: self._jump_to_path(jump.value))
            except Exception:
                pass
            if platform.system() != "Windows" and os.path.isdir("/tmp"):
                ui.button("/tmp", on_click=lambda: self._navigate_to_directory("/tmp")).classes(
                    "shrink-0"
                )

    def _create_file_list_area(self):
        """Create the file list container."""
        self.drive_container = ui.column().classes('mx-3 my-2')
        # Ensure items are left-aligned and text is left-justified
        self.file_list = ui.column().classes('bg-white border-t border-gray-200 max-h-96 overflow-auto items-start text-left')

    def _create_footer(self):
        """Create the dialog footer with action buttons."""
        with ui.row().classes('bg-gray-50 border-t p-4 justify-between items-center'):
            with ui.column().classes('flex-1'):
                ui.label(f'Current: {Path(self.state["current_path"]).name or "Root"}').classes('text-sm text-gray-600')

            with ui.row().classes('gap-2'):
                ui.button(
                    'Cancel',
                    on_click=self.dialog.close
                ).classes('px-6 py-2 bg-gray-100 border border-gray-300 text-gray-800 hover:bg-gray-50 rounded-lg transition-colors')

                ui.button(
                    'Select Folder',
                    on_click=self._select_current_directory
                ).classes('px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium')

    def _navigate_up(self):
        """Navigate to parent directory."""
        parent_path = str(Path(self.state['current_path']).parent)
        self._render_directory_tree(parent_path)

    def _refresh_current(self):
        """Refresh the current directory listing."""
        self._render_directory_tree(self.state['current_path'])

    def _navigate_to_directory(self, path: str):
        """Navigate to a specific directory."""
        self._render_directory_tree(path)

    def _render_directory_tree(self, current_path: str):
        """Render directory listing: subfolders (navigable) then files in this folder (read-only rows)."""
        self.file_list.clear()
        self.state['current_path'] = current_path
        jump = getattr(self, "_path_jump_input", None)
        if jump is not None:
            try:
                jump.value = current_path
            except Exception:
                pass

        path_obj = Path(current_path)
        # Validate path
        if not path_obj.exists():
            with self.file_list:
                ui.label('Directory does not exist').classes('text-red-600')
            return

        # Parent directory button (if not root)
        if path_obj.parent != path_obj:
            parent_path = str(path_obj.parent)
            with self.file_list:
                ui.button(
                    'navigate_up',
                    on_click=lambda p=parent_path: self._navigate_to_directory(p)
                ).classes('w-full justify-start p-3 hover:bg-blue-50 border-b border-gray-100 text-blue-600').props('flat icon=arrow_upward prepend-icon')

        try:
            items = sorted(path_obj.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            directories = [p for p in items if p.is_dir()]
            files = [p for p in items if p.is_file()]

            for directory in directories:
                dir_path = str(directory)
                with self.file_list:
                    row = ui.row().classes('w-full items-center p-3 hover:bg-blue-50 border-b border-gray-100 cursor-pointer')
                    try:
                        row.on('click', lambda e, p=dir_path: self._navigate_to_directory(p))
                    except Exception:
                        pass
                    with row:
                        ui.icon('folder').classes('text-yellow-500 mr-3')
                        ui.label(directory.name).classes('truncate flex-1 text-left')

            for file_path in files:
                with self.file_list:
                    with ui.row().classes(
                        'w-full items-center p-3 border-b border-gray-100 bg-gray-50/80'
                    ):
                        ui.icon('insert_drive_file').classes('text-gray-500 mr-3 shrink-0')
                        ui.label(file_path.name).classes('truncate flex-1 text-left text-gray-700')

            if not directories and not files:
                with self.file_list:
                    ui.label('Empty folder').classes('text-gray-500 p-3 text-center')

        except PermissionError:
            with self.file_list:
                ui.label('Permission denied').classes('text-red-600')
        except OSError:
            with self.file_list:
                ui.label('Cannot access directory').classes('text-red-600')

    def _handle_drive_change(self, drive: str):
        """Handle Windows drive change."""
        self._navigate_to_directory(drive)

    def _select_current_directory(self):
        """Validate and select the current directory."""
        path = self.state['current_path']
        try:
            expanded_path = Path(path).expanduser()
            dir_input = DirectoryInput(path=expanded_path)
            self.on_select(str(dir_input.path))
            self.dialog.close()
        except (ValidationError, ValueError, TypeError) as e:
            ui.notify(f'Invalid directory: {str(e)}', type='negative')

    def show(self):
        """Show the directory browser dialog."""
        logger.info("Opening directory browser (initial_path: %s)", self.initial_path)

        with ui.dialog() as self.dialog, ui.card().classes('w-[900px] shadow-2xl border-0 rounded-xl overflow-hidden'):
            self._create_dialog_header()
            self._create_navigation_bar()
            self._create_file_list_area()
            self._create_footer()

            # Setup drive selection and initial rendering
            _add_windows_drives_toggle(self.drive_container, self._handle_drive_change, self.state['current_path'])
            self._render_directory_tree(self.state['current_path'])

        self.dialog.open()


def browse_directory(on_select: Callable[[str], None], initial_path: Optional[str] = None):
    """
    Open a directory browser dialog using NiceGUI components.

    Creates a modal dialog with file/folder listing, navigation, and selection
    capabilities. Supports Windows drive selection and cross-platform path handling.

    Args:
        on_select (Callable[[str], None]): Callback function called when a directory is selected.
            Receives the selected directory path as a string
        initial_path (Optional[str]): Initial directory to start browsing from.
            Supports user expansion (e.g., ~/Documents). Defaults to current working directory

    Returns:
        None: Dialog is displayed modally

    Examples:
        >>> browse_directory(
        ...     on_select=lambda path: print(f"Selected: {path}"),
        ...     initial_path="~/Documents"
        ... )

    Tips:
        - Uses Pydantic DirectoryInput for path validation
        - Supports Windows drive selection on Windows
        - Paths are expanded (user home directory, etc.)
        - Dialog is modal and blocks until selection or cancellation
    """
    browser = DirectoryBrowser(on_select, initial_path)
    browser.show()


class FileBrowser:
    """Refactored file browser with clean separation of concerns."""

    def __init__(self, on_select: Callable[[str], None], initial_path: Optional[str] = None,
                 filetypes: Optional[list] = None):
        self.on_select = on_select
        self.initial_path = initial_path
        self.filetypes = filetypes or []
        self.state = {'current_path': self._get_start_path(), 'selected_file': None}
        self.dialog = None
        self.path_input = None
        self.file_list = None
        self.drive_container = None
        self.selected_display = None

    def _get_start_path(self) -> str:
        """Prefer an existing folder (or parent of an existing file); else demo; else cwd."""
        cand = _resolved_file_browser_folder(self.initial_path)
        if cand:
            return cand
        try:
            from frontend.utils.nicegui_storage import resolve_demo_folder_for_browser
            demo = resolve_demo_folder_for_browser()
            if demo:
                return demo
        except Exception as e:
            logger.debug("Could not resolve demo folder for browser: %s", e)
        return os.getcwd()

    def _create_dialog_header(self):
        """Create the dialog header with title."""
        try:
            from frontend.components.file_browser.header import render_file_browser_header
            render_file_browser_header("Select File", icon='description')
        except (ImportError, ModuleNotFoundError):
            with ui.row().classes('bg-gradient-to-r from-green-600 to-green-700 text-white p-4 items-center'):
                ui.icon('description', size='2rem').classes('mr-3')
                ui.label('Select File').classes('text-xl font-semibold')

    def _jump_to_path_file(self, raw: str) -> None:
        """Jump file browser to a folder (same as directory browser for UFDR paths)."""
        s = (raw or "").strip()
        if not s:
            ui.notify("Enter a folder path", type="warning")
            return
        try:
            p = Path(s).expanduser()
            if not p.is_absolute():
                p = Path(os.getcwd()) / p
            rp = str(p.resolve())
            if not os.path.isdir(rp):
                ui.notify(f"Not a directory or not accessible: {rp}", type="negative")
                return
            self._update_file_list(rp)
        except OSError as e:
            ui.notify(f"Invalid path: {e}", type="negative")

    def _create_navigation_bar(self):
        """Create the navigation bar with address bar and buttons."""
        with ui.row().classes('bg-gray-50 border-b p-3 items-center gap-2'):
            ui.icon('home', size='1.2rem').classes('text-gray-500')
            ui.icon('chevron_right', size='1.2rem').classes('text-gray-400')

            # Current path display
            self.path_input = ui.input(
                value=self.state['current_path'],
                placeholder='Current directory...'
            ).classes('flex-1 border border-gray-300 rounded px-3 py-1 text-sm bg-gray-50').props('readonly')
            self.path_input.bind_value_from(self.state, 'current_path')

            # Navigation buttons
            ui.button(
                icon='arrow_upward',
                on_click=self._navigate_up
            ).classes('px-2 py-1 text-gray-600 hover:bg-gray-200 rounded').props('flat dense')

            ui.button(
                icon='refresh',
                on_click=self._refresh_current
            ).classes('px-2 py-1 text-gray-600 hover:bg-gray-200 rounded').props('flat dense')
            # Also render a full-path label below the address bar that wraps for long paths
            try:
                self.full_path_label = ui.label(self.state['current_path']).classes('text-xs font-mono text-gray-600 mt-1 break-words')
                self.full_path_label.bind_text_from(self.state, 'current_path')
            except Exception:
                pass
        with ui.row().classes('bg-gray-50 border-b px-3 pb-3 pt-0 items-center gap-2 flex-wrap'):
            fjump = ui.input(
                placeholder="Paste folder path (e.g. /tmp/case123/files/Image) — Enter or Go",
                value=self.state["current_path"],
            ).classes("flex-1 min-w-[12rem]").props("outlined dense")
            self._path_jump_input = fjump
            ui.button("Go", on_click=lambda: self._jump_to_path_file(fjump.value)).classes("shrink-0")
            try:
                fjump.on("keydown.enter", lambda: self._jump_to_path_file(fjump.value))
            except Exception:
                pass
            if platform.system() != "Windows" and os.path.isdir("/tmp"):
                ui.button("/tmp", on_click=lambda: self._navigate_to_directory("/tmp")).classes(
                    "shrink-0"
                )

    def _create_file_list_area(self):
        """Create the file list container."""
        self.drive_container = ui.column().classes('mx-3 my-2')
        # assign an id to the file list so we can control scrolling via JS
        self._file_list_id = f"file_list_{id(self)}"
        self.file_list = ui.column().classes('bg-white border-t border-gray-200 max-h-96 overflow-auto').props(f"id={self._file_list_id}")

    def _create_footer(self):
        """Create the dialog footer with file info and action buttons."""
        with ui.row().classes('bg-gray-50 border-t p-4 justify-between items-center'):
            with ui.column().classes('flex-1'):
                self._update_selected_display()

            with ui.row().classes('gap-2'):
                ui.button(
                    'Cancel',
                    on_click=self.dialog.close
                ).classes('px-6 py-2 bg-gray-100 border border-gray-300 text-gray-800 hover:bg-gray-50 rounded-lg transition-colors')

                ui.button(
                    'Select File',
                    on_click=self._select_file_path
                ).classes('px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium')

    def _update_selected_display(self):
        """Update the selected file display in the footer."""
        selected = self.state.get('selected_file')
        if selected:
            file_name = Path(selected).name
            filter_info = f"Filtered: {', '.join(self.filetypes)}" if self.filetypes else "All files"
            display_text = f'Selected: {file_name} | {filter_info}'
        else:
            filter_info = f"Filtered: {', '.join(self.filetypes)}" if self.filetypes else "All files"
            display_text = f'Filter: {filter_info}'

        if self.selected_display:
            self.selected_display.text = display_text
        else:
            self.selected_display = ui.label(display_text).classes('text-sm text-gray-600')

    def _navigate_up(self):
        """Navigate to parent directory."""
        parent_path = str(Path(self.state['current_path']).parent)
        self._update_file_list(parent_path)

    def _refresh_current(self):
        """Refresh the current directory listing."""
        self._update_file_list(self.state['current_path'])

    def _navigate_to_directory(self, path: str):
        """Navigate to a directory."""
        self._update_file_list(path)

    def _update_file_list(self, path: str):
        """Update the file list with contents of the given path."""
        self.file_list.clear()
        self.state['current_path'] = path
        self.state['selected_file'] = None
        try:
            if getattr(self, 'path_input', None):
                self.path_input.value = path
        except Exception:
            pass
        j = getattr(self, "_path_jump_input", None)
        if j is not None:
            try:
                j.value = path
            except Exception:
                pass

        path_obj = Path(path)

        # Validate path
        if not path_obj.exists() or not path_obj.is_dir():
            with self.file_list:
                ui.label('Invalid directory path').classes('text-red-600')
            self._update_selected_display()
            return

        # Parent directory button
        if path_obj.parent != path_obj:
            parent_path = str(path_obj.parent)
            with self.file_list:
                ui.button(
                    'arrow_upward',
                    on_click=lambda p=parent_path: self._navigate_to_directory(p)
                ).classes('w-full justify-start p-3 hover:bg-blue-50 border-b border-gray-100 text-blue-600').props('flat icon=arrow_upward prepend-icon')

        # List items
        try:
            items = sorted(path_obj.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

            for item in items:
                if item.is_dir():
                    # Directory
                    dir_path = str(item)
                    with self.file_list:
                        row = ui.row().classes('w-full items-center p-3 hover:bg-blue-50 border-b border-gray-100 cursor-pointer')
                        try:
                            row.on('click', lambda e, p=dir_path: self._navigate_to_directory(p))
                        except Exception:
                            pass
                        with row:
                            ui.icon('folder').classes('text-yellow-500 mr-3')
                            ui.label(item.name).classes('truncate flex-1 text-left')
                else:
                    # File - check filter
                    if self.filetypes and item.suffix.lower() not in [ft.lower() for ft in self.filetypes]:
                        continue

                    file_path = str(item)
                    with self.file_list:
                        ui.button(
                            item.name,
                            on_click=lambda fp=file_path: self._select_file(fp)
                        ).classes('w-full justify-start p-3 hover:bg-green-50 border-b border-gray-100 text-left').props('flat icon=insert_drive_file prepend-icon')

            # If no items, show message
            if not any(items):
                with self.file_list:
                    ui.label('No files or directories').classes('text-gray-500 p-3 text-center')

        except PermissionError:
            with self.file_list:
                ui.label('Permission denied').classes('text-red-600')
        except OSError:
            with self.file_list:
                ui.label('Cannot access directory').classes('text-red-600')

        # Scroll the file list to top so the newly-rendered subdirectory is visible at the top
        try:
            # Simplified: target the known file list element and smooth-scroll to top
            ui.run_javascript(f"setTimeout(()=>{{const el=document.getElementById('{getattr(self, '_file_list_id', '')}'); if(el && el.scrollTo) el.scrollTo({{top:0, behavior:'smooth'}}); else if(el) el.scrollTop=0;}}, 80);")
        except Exception:
            pass
        self._update_selected_display()

    def _select_file(self, file_path: str):
        """Select a file."""
        self.state['selected_file'] = file_path
        self._update_selected_display()

        # Visual feedback
        ui.notify(f'Selected: {Path(file_path).name}', type='info', timeout=1000)

    def _handle_drive_change(self, drive: str):
        """Handle Windows drive change."""
        self._navigate_to_directory(drive)

    def _select_file_path(self):
        """Validate and select the currently selected file."""
        selected_file = self.state.get('selected_file')
        if selected_file:
            try:
                file_input = FileInput(path=Path(selected_file))
                self.on_select(str(file_input.path))
                self.dialog.close()
            except (ValidationError, ValueError, TypeError) as e:
                ui.notify(f'Invalid file: {str(e)}', type='negative')
        else:
            ui.notify('Please select a file first', type='warning')

    def show(self):
        """Show the file browser dialog."""
        logger.info("Opening file browser (initial_path: %s, filetypes: %s)",
                   self.initial_path, self.filetypes)

        with ui.dialog() as self.dialog, ui.card().classes('w-[900px] shadow-2xl border-0 rounded-xl overflow-hidden'):
            self._create_dialog_header()
            self._create_navigation_bar()
            self._create_file_list_area()
            self._create_footer()

            # Setup drive selection and initial rendering
            _add_windows_drives_toggle(self.drive_container, self._handle_drive_change, self.state['current_path'])
            self._update_file_list(self.state['current_path'])

        self.dialog.open()


def browse_file(on_select: Callable[[str], None], initial_path: Optional[str] = None,
                filetypes: Optional[list] = None):
    """
    Open a file browser dialog using NiceGUI components.

    Creates a modal dialog for file selection with navigation, filtering,
    and selection capabilities. Similar to browse_directory but for files.

    Args:
        on_select (Callable[[str], None]): Callback function called when a file is selected.
            Receives the selected file path as a string
        initial_path (Optional[str]): Initial directory to start browsing from.
            Supports user expansion (e.g., ~/Documents). Defaults to current working directory
        filetypes (Optional[list]): List of file extensions to filter (e.g., ['.txt', '.jpg']).
            Only files matching these extensions will be selectable. Defaults to None (all files)

    Returns:
        None: Dialog is displayed modally

    Examples:
        >>> browse_file(
        ...     on_select=lambda path: print(f"Selected: {path}"),
        ...     initial_path="~/Documents",
        ...     filetypes=['.txt', '.pdf']
        ... )

    Tips:
        - Uses Pydantic FileInput for path validation
        - Supports Windows drive selection on Windows
        - File filtering by extension is optional
        - Dialog is modal and blocks until selection or cancellation
    """
    browser = FileBrowser(on_select, initial_path, filetypes)
    browser.show()


# Duplicate function removed
def browse_directory_simple(
    input_field: ui.input,
    initial_path: Optional[str] = None,
    on_after_select: Optional[Callable[[], None]] = None,
):
    """
    Open a simple directory browser that updates an input field.
    
    Convenience wrapper around browse_directory that automatically updates
    a NiceGUI input field with the selected directory path.
    
    Args:
        input_field (ui.input): NiceGUI input widget to update with selected path
        initial_path (Optional[str]): Initial directory to start browsing from.
            If omitted, uses the text already in ``input_field`` (so pasted UFDR paths open there).
        on_after_select: Optional callback after the path is set (e.g. re-run validation;
            ``set_value`` may not emit ``change``).
    
    Returns:
        None
    
    Examples:
        >>> dir_input = ui.input(label='Directory')
        >>> ui.button('Browse', on_click=lambda: browse_directory_simple(dir_input))
    
    Tips:
    - Updates input_field.value with selected path
    - Simple wrapper for form integration
    - Uses browse_directory internally
    """
    if initial_path is None:
        try:
            typed = (input_field.value or "").strip()
            initial_path = typed or None
        except Exception:
            initial_path = None
    logger.debug("Opening simple directory browser (initial_path: %s)", initial_path)
    def on_select(path: str):
        # Use set_value so any `on('change')` handlers are triggered
        try:
            input_field.set_value(path)
        except AttributeError:
            # Fallback to direct assignment if set_value not available
            input_field.value = path
        if on_after_select is not None:
            try:
                on_after_select()
            except Exception as e:
                logger.debug("browse_directory_simple on_after_select: %s", e)

    browse_directory(on_select, initial_path)


def browse_file_simple(
    input_field: ui.input,
    initial_path: Optional[str] = None,
    filetypes: Optional[list] = None,
    on_after_select: Optional[Callable[[], None]] = None,
):
    """
    Open a simple file browser that updates an input field
    
    Args:
        input_field: NiceGUI input field to update with selected path
        initial_path: Initial directory to start browsing from (defaults to parent of typed path if any)
        filetypes: List of file extensions to filter
        on_after_select: Optional callback after the path is set (e.g. re-run validation).
    """
    if initial_path is None:
        try:
            typed = (input_field.value or "").strip()
            if typed:
                p = Path(typed).expanduser()
                if p.is_file():
                    initial_path = str(p.parent)
                elif p.is_dir():
                    initial_path = str(p)
        except Exception:
            initial_path = None
    def on_select(path: str):
        # Use set_value so any `on('change')` handlers are triggered
        try:
            input_field.set_value(path)
        except AttributeError:
            input_field.value = path
        if on_after_select is not None:
            try:
                on_after_select()
            except Exception as e:
                logger.debug("browse_file_simple on_after_select: %s", e)

    browse_file(on_select, initial_path, filetypes)