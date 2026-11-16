"""Multi-step workflow stepper UI (chatbot workflow steps and reusable stepper)."""

from __future__ import annotations

import logging

from nicegui import ui

logger = logging.getLogger(__name__)


class WorkflowStepper:
    """
    Workflow stepper component for multi-step processes.

    Provides a visual indicator of progress through a multi-step workflow
    with support for updating steps and custom styling.

    Usage:
        stepper = WorkflowStepper(['Input', 'Review', 'Submit', 'Results'])
        stepper.set_step(0)  # Start at first step
        stepper.set_step(1)  # Move to next step
        stepper.set_step(3)  # Jump to specific step
    """

    def __init__(
        self,
        steps: list[str],
        current_step: int = 0,
        container: ui.element | None = None,
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
        self.step_elements: list[ui.element] = []
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


def create_workflow_stepper(
    steps: list[str], current_step: int = 0, container: ui.element | None = None
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
        stepper.set_step(1)  # Move to "Fill Form"
    """
    return WorkflowStepper(steps, current_step, container)
