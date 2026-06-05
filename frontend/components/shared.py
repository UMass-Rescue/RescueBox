import logging
from typing import List, Dict, Optional
import sys
from nicegui import ui
from frontend.utils.ui import notify_success as _ns, notify_error as _ne
from frontend.utils.ui import notify_info as _ni, notify_warning as _nw
from frontend.config import APP_TITLE, APP_VERSION
import frontend.constants as constants
from frontend.design_tokens import Design
from frontend.utils import get_user_id_for_jobs

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

"""
Breadcrumb Navigation Component

This module provides breadcrumb navigation for better UX and quick navigation
between related pages (e.g., Jobs > Job Details > Results > Submit).
"""


def notify_success(message: str, **kwargs):
    logger.debug(f"Success notification shown: {message}")
    return _ns(message, **kwargs)


def notify_error(message: str, **kwargs):
    logger.debug(f"Error notification shown: {message}")
    return _ne(message, **kwargs)


def notify_info(message: str, **kwargs):
    logger.debug(f"Info notification shown: {message}")
    return _ni(message, **kwargs)


def notify_warning(message: str, **kwargs):
    logger.debug(f"Warning notification shown: {message}")
    return _nw(message, **kwargs)


notifications = sys.modules[__name__]
navbar = sys.modules[__name__]
breadcrumbs = sys.modules[__name__]
stepper = sys.modules[__name__]


def create_breadcrumbs(items: List[Dict[str, Optional[str]]], container=None):
    """
    Create breadcrumb navigation component.

    Creates a breadcrumb trail showing the navigation path with links.
    The last item is displayed as plain text (current page).
    """
    logger.debug("Creating breadcrumbs with %d items", len(items))

    if container:
        breadcrumb_container = container
    else:
        breadcrumb_container = ui.row().classes("items-center gap-2 mb-4 text-sm")

    with breadcrumb_container:
        for i, item in enumerate(items):
            label = item.get("label", "")
            link = item.get("link")

            if link:
                # Add link with hover effect
                ui.link(label, link).classes("text-[#881c1c] hover:underline")
            else:
                # Current page (no link)
                ui.label(label).classes("text-zinc-600 font-semibold")

            # Add separator (>) except for last item
            if i < len(items) - 1:
                ui.label(">").classes("text-zinc-400 mx-1")

    logger.debug("Breadcrumbs created successfully")
    return breadcrumb_container


def create_job_breadcrumbs(job_id: str, current_page: str = "Results"):
    """
    Create breadcrumbs for job-related pages.

    Convenience function for creating job breadcrumbs with common navigation.

    """
    items = [
        {"label": "Jobs", "link": "/jobs"},
        {"label": f"Job {job_id[:8]}...", "link": f"/jobs/{job_id}"},
        {"label": current_page},
    ]
    return create_breadcrumbs(items)


"""
Navigation Bar Component

This module provides the main navigation bar component used across all pages
in the RescueBox Desktop application. The navbar provides consistent navigation
and branding throughout the application.

Key features:
- Sticky positioning (stays visible when scrolling)
- Responsive layout
- Accessible navigation links
- Consistent branding
"""


def create_navbar():
    """
    Create and render the main navigation bar component.

    This function generates a sticky navigation bar that appears at the top
    of every page. It includes the RescueBox branding and navigation links
    to major sections of the application.

    """
    # logger.info("Creating navigation bar component")

    with ui.header(wrap=False).classes(Design.NAV_HEADER):
        # logger.debug("Header created with sticky positioning and blue theme")

        _link_cls = Design.NAV_LINK
        _nav_locked = get_user_id_for_jobs() is None

        def _nav_blocked_msg():
            ui.notify(
                "Please select or create an active Case on the home page.",
                type="warning",
                classes="rb-notify-505759",
            )

        from frontend.utils import get_active_case
        active_case = get_active_case()

        with ui.row().classes(
            "w-full min-w-0 min-h-12 h-auto sm:h-14 px-2 sm:px-3 py-0 items-center gap-2 sm:gap-3 "
            "box-border flex-wrap sm:flex-nowrap justify-start"
        ):
            # logger.debug("Creating navbar container with responsive layout")

            with ui.row().classes("shrink-0 items-center gap-2 min-w-0"):
                with ui.row().classes("items-center cursor-pointer").on("click", lambda _: ui.navigate.to("/")):
                    ui.html('<img src="/icons/logo.png" class="h-8 sm:h-9 md:h-10 w-auto object-contain shrink-0" />', sanitize=False)
                if active_case:
                    from frontend.database import get_case_db
                    from frontend.utils import set_active_case_id, clear_active_case_id
                    
                    try:
                        all_cases = get_case_db().get_all_cases_sync()
                        other_cases = [c for c in all_cases if c.caseId != active_case.caseId]
                    except Exception:
                        all_cases = [active_case]
                        other_cases = []

                    if len(all_cases) <= 1:
                        # Just show a clean static badge if there is only one case in the system
                        with ui.row().classes("items-center gap-1 bg-black/20 px-2.5 py-1 rounded-lg border border-white/20 ml-2 cursor-pointer").on("click", lambda _: ui.navigate.to("/case")):
                            ui.icon("folder", size="xs").classes("text-white")
                            ui.label(f"Case: {active_case.caseNumber}").classes("text-xs font-semibold text-white")
                    else:
                        # Show the interactive dropdown if there are multiple cases to switch between
                        with ui.dropdown_button(
                            f"Case: {active_case.caseNumber}",
                            icon="folder",
                            color=None,
                            auto_close=True,
                        ).classes(
                            "text-xs font-semibold text-white bg-black/20 px-2.5 py-1 rounded-lg border border-white/20 ml-2 cursor-pointer"
                        ).props("flat dense no-caps split").on("click", lambda _: ui.navigate.to("/case")):
                            ui.menu_item("Case Overview", on_click=lambda: ui.navigate.to("/case")).classes("font-semibold text-[#881c1c]")
                            ui.separator()
                            if other_cases:
                                ui.label("Switch Case:").classes("text-[10px] font-bold text-slate-400 px-3 py-1 uppercase tracking-wider")
                                for c in other_cases[:5]: # Show up to 5 other cases
                                    def _switch_case(cid=c.caseId):
                                        set_active_case_id(cid)
                                        ui.notify(f"Switched to case {c.caseNumber}.", type="positive")
                                        ui.timer(0.3, lambda: ui.navigate.to("/case"), once=True)
                                    ui.menu_item(c.caseNumber, on_click=_switch_case)
                                ui.separator()
                            
                            def _close_active_case():
                                clear_active_case_id()
                                ui.notify("Case closed.", type="info")
                                ui.timer(0.2, lambda: ui.navigate.to("/"), once=True)
                            
                            ui.menu_item("Close Case", on_click=_close_active_case).classes("text-rose-500 font-semibold")

            with ui.row().classes("min-w-0 flex-1 justify-end items-center"):
                with ui.row().classes(
                    "inline-flex flex-wrap items-center justify-end gap-x-0.5 gap-y-0 "
                    "max-w-full py-0"
                ):
                    # logger.debug("Creating navigation links row")

                    _nav_items = (
                        ("Assistant", "/chatbot"),
                        ("Jobs", "/jobs"),
                        ("Logs", "/logs"),
                    )
                    for label, path in _nav_items:
                        if _nav_locked:
                            ui.label(label).classes(
                                _link_cls + " opacity-50 cursor-not-allowed select-none"
                            ).on("click", lambda _: _nav_blocked_msg())
                        else:
                            ui.link(label, path).classes(_link_cls)

                    def _open_about() -> None:
                        ui.navigate.to(constants.NAV_LINKS["about"])

                    def _open_readme() -> None:
                        if _nav_locked:
                            _nav_blocked_msg()
                        else:
                            ui.navigate.to("/models")

                    def _open_demo() -> None:
                        ui.navigate.to("/demo")

                    with ui.dropdown_button(
                        "Resources",
                        color=None,
                        auto_close=True,
                    ).classes(_link_cls).props("flat dense no-caps"):
                        ui.menu_item("Readme", on_click=_open_readme)
                        ui.menu_item("About", on_click=_open_about)

                # Session display removed for demo safety (avoids accidental user actions)

                # Clear Session button removed to avoid accidental data loss


def render_loading_row(message: str = "Loading..."):
    """Render a small loading row with spinner and label."""
    from frontend.utils.ui import _safe_ui_call

    row = _safe_ui_call(ui.row)
    if not row:
        return None
    with row.classes("items-center gap-2"):
        ui.spinner(size="sm")
        ui.label(message).classes("text-sm text-zinc-600")
    return row


def render_error_card(container, message: str):
    """Render an error card inside the given container."""
    with container:
        with ui.card().classes("bg-red-50 border border-red-300 p-4") as error_card:
            ui.label("Error").classes("text-lg font-semibold text-red-700 mb-2")
            ui.label(message).classes("text-red-600")
    return error_card


def render_success_card(container, message: str):
    """Render a success card inside the given container."""
    with container:
        with ui.card().classes(
            "bg-green-50 border border-green-300 p-4"
        ) as success_card:
            ui.label("Success").classes("text-lg font-semibold text-green-700 mb-2")
            ui.label(message).classes("text-green-600")
    return success_card


"""
Enhanced Notification System

This module provides an enhanced notification system with better styling,
positioning, and user preferences support.

Usage:
    from frontend.components.shared import notify_success, notify_error, notify_info
    
    notify_success("Job submitted successfully")
    notify_error("Failed to submit job")
    notify_info("Processing your request...")
"""


def render_page_header(title: str, actions_callable: Optional[callable] = None):
    """Render a standardized page header with title and optional action buttons area."""
    with ui.row().classes("items-center justify-between w-full mb-6"):
        ui.label(title).classes("text-4xl font-bold")
        with ui.row().classes("gap-2"):
            if actions_callable:
                try:
                    actions_callable()
                except Exception as e:
                    logger.exception("Error rendering header actions: %s", e)
            else:
                # default placeholder
                ui.label("")


"""
Stepper Component for Multi-Step Workflows

This module provides a stepper component to visualize multi-step workflows
and enhance user experience by showing progress through complex processes.

Usage:
    from frontend.components.shared import create_workflow_stepper
    
    steps = ['Step 1', 'Step 2', 'Step 3']
    stepper = create_workflow_stepper(steps, current_step=0)
"""


class WorkflowStepper:
    """
    Workflow stepper component for multi-step processes.

    Provides a visual indicator of progress through a multi-step workflow
    with support for updating steps and custom styling.

    Usage:
        stepper = WorkflowStepper(['Input', 'Review', 'Submit', 'Results'])
        stepper.set_step(0)  # Start at first step
        stepper.next_step()  # Move to next step
        stepper.set_step(3)  # Jump to specific step
    """

    def __init__(
        self,
        steps: List[str],
        current_step: int = 0,
        container: Optional[ui.element] = None,
    ):
        """
        Initialize workflow stepper.

        Args:
            steps: List of step names
            current_step: Initial step index (0-based)
            container: Optional container to render into

        Returns:
            None
        """
        self.steps = steps
        self.current_step = current_step
        self.step_elements: List[ui.element] = []
        self.container = container or ui.column()

        logger.info("Creating workflow stepper with %d steps", len(steps))
        self._render()
        logger.debug("Workflow stepper rendered")

    def _render(self):
        """Render the stepper UI."""
        # Skip rendering if container is a mock (test mode)
        if hasattr(self.container, "_mock_name") or hasattr(
            self.container, "_mock_children"
        ):
            return

        with self.container:
            with ui.row().classes("w-full items-center justify-center p-4"):
                for i, step_name in enumerate(self.steps):
                    # Step circle and label
                    step_container = ui.column().classes("items-center flex-1 max-w-xs")

                    with step_container:
                        # Step circle with number
                        circle_classes = self._get_circle_classes(i)
                        circle = (
                            ui.element("div")
                            .classes(circle_classes)
                            .style(
                                "width: 40px; height: 40px; border-radius: 50%; display: flex; "
                                "align-items: center; justify-content: center; font-weight: bold; "
                                "margin-bottom: 8px;"
                            )
                        )
                        with circle:
                            if i < self.current_step:
                                # Completed step - show checkmark
                                ui.icon("check", size="sm").classes("text-white")
                            else:
                                # Show step number
                                ui.label(str(i + 1)).classes(
                                    "text-white"
                                    if i == self.current_step
                                    else "text-zinc-500"
                                )

                        # Step label
                        label_classes = self._get_label_classes(i)
                        ui.label(step_name).classes(label_classes).classes(
                            "text-center text-sm"
                        )

                        # Connector line (except for last step)
                        if i < len(self.steps) - 1:
                            line_classes = self._get_line_classes(i)
                            ui.element("div").classes(line_classes).style(
                                "width: 100%; height: 2px; margin-top: -20px; margin-left: 50%;"
                            )

                    self.step_elements.append(step_container)

    def _get_circle_classes(self, index: int) -> str:
        """Get CSS classes for step circle."""
        if index < self.current_step:
            return "bg-green-500"  # Completed
        elif index == self.current_step:
            return (
                "rb-brand-step-current"  # UMass Maroon #881c1c — see ui_readability_css
            )
        else:
            return "bg-zinc-300"  # Pending

    def _get_label_classes(self, index: int) -> str:
        """Get CSS classes for step label."""
        if index <= self.current_step:
            return "font-semibold text-zinc-800"
        else:
            return "text-zinc-400"

    def _get_line_classes(self, index: int) -> str:
        """Get CSS classes for connector line."""
        if index < self.current_step:
            return "bg-green-500"  # Completed path
        else:
            return "bg-zinc-300"  # Pending path

    def set_step(self, step_index: int):
        """
        Set current step by index.

        Args:
            step_index: Step index (0-based)

        Returns:
            None

        Raises:
            ValueError: If step_index is out of range
        """
        if not 0 <= step_index < len(self.steps):
            raise ValueError(
                f"Step index {step_index} out of range [0, {len(self.steps)})"
            )

        logger.info(
            "Setting stepper to step %d: %s", step_index, self.steps[step_index]
        )
        self.current_step = step_index
        # Re-render to update UI
        self.container.clear()
        self.step_elements.clear()
        self._render()

    def next_step(self):
        """
        Move to next step.

        Returns:
            None
        """
        if self.current_step < len(self.steps) - 1:
            self.set_step(self.current_step + 1)
        else:
            logger.warning("Already at last step")

    def previous_step(self):
        """
        Move to previous step.

        Returns:
            None
        """
        if self.current_step > 0:
            self.set_step(self.current_step - 1)
        else:
            logger.warning("Already at first step")

    def get_current_step_name(self) -> str:
        """
        Get name of current step.

        Returns:
            Current step name
        """
        return self.steps[self.current_step]

    def is_complete(self) -> bool:
        """
        Check if all steps are complete.

        Returns:
            True if at last step
        """
        return self.current_step >= len(self.steps) - 1


def create_workflow_stepper(
    steps: List[str], current_step: int = 0, container: Optional[ui.element] = None
) -> WorkflowStepper:
    """
    Create a workflow stepper component.

    Convenience function for creating a WorkflowStepper instance.

    Args:
        steps: List of step names
        current_step: Initial step index (0-based)
        container: Optional container to render into

    Returns:
        WorkflowStepper instance

    Usage:
        stepper = create_workflow_stepper(
            ['Select Tool', 'Fill Form', 'Submit', 'View Results'],
            current_step=0
        )
        stepper.next_step()  # Move to "Fill Form"
    """
    return WorkflowStepper(steps, current_step, container)


"""
Example: Using Stepper Component in Chatbot Workflow

This file demonstrates how to integrate the WorkflowStepper component
into the chatbot interface to show progress through the workflow.

Workflow Steps:
1. Message Sent - User sends message
2. Tool Selection - Assistant selects tool
3. Form Filled - User fills form
4. Job Submitted - Form submitted
5. Results Ready - Results displayed

Usage:
    See chatbot.py for integration example
"""

# Define workflow steps for chatbot
CHATBOT_WORKFLOW_STEPS = [
    "Message Sent",
    "Tool Selected",
    "Form Ready",
    "Submitting",
    "Results Ready",
]


def create_chatbot_stepper(container: ui.element) -> WorkflowStepper:
    """
    Create stepper for chatbot workflow.

    Args:
        container: Container to render stepper into

    Returns:
        WorkflowStepper instance
    """
    return WorkflowStepper(
        steps=CHATBOT_WORKFLOW_STEPS, current_step=0, container=container
    )


navbar = create_navbar
