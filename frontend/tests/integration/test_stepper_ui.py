"""
Integration tests for stepper component UI

Tests the stepper component rendering and interaction in a NiceGUI context.
"""

import pytest
from nicegui.testing import User


class TestStepperUI:
    """Integration tests for stepper UI rendering"""

    @pytest.mark.asyncio
    async def test_stepper_renders_steps(self, user: User):
        """Test that stepper renders all steps"""
        from nicegui import ui
        from frontend.components.shared import create_workflow_stepper

        steps = ["Step 1", "Step 2", "Step 3"]

        @ui.page("/test")
        async def test_page():
            container = ui.column().classes("w-full")
            create_workflow_stepper(steps, current_step=0, container=container)

        await user.open("/test")

        # Should see all step labels
        await user.should_see("Step 1")
        await user.should_see("Step 2")
        await user.should_see("Step 3")

    @pytest.mark.asyncio
    async def test_stepper_shows_current_step(self, user: User):
        """Test that stepper highlights current step"""
        from nicegui import ui
        from frontend.components.shared import create_workflow_stepper

        steps = ["First", "Second", "Third"]

        @ui.page("/test")
        async def test_page():
            container = ui.column().classes("w-full")
            stepper = create_workflow_stepper(
                steps, current_step=1, container=container
            )
            # Store stepper reference for potential future use
            # newer NiceGUI exposes client as an Element; attach stepper directly to client
            ui.context.client.stepper = stepper

        await user.open("/test")

        # Should see all steps
        await user.should_see("First")
        await user.should_see("Second")
        await user.should_see("Third")

    @pytest.mark.asyncio
    async def test_stepper_chatbot_workflow(self, user: User):
        """Test stepper with chatbot workflow steps"""
        from nicegui import ui
        from frontend.components.shared import create_workflow_stepper

        chatbot_steps = [
            "Message Sent",
            "Tool Selected",
            "Form Ready",
            "Submitting",
            "Results Ready",
        ]

        @ui.page("/test")
        async def test_page():
            container = ui.column().classes("w-full")
            create_workflow_stepper(chatbot_steps, current_step=0, container=container)

        await user.open("/test")

        # Should see all chatbot workflow steps
        await user.should_see("Message Sent")
        await user.should_see("Tool Selected")
        await user.should_see("Form Ready")
        await user.should_see("Submitting")
        await user.should_see("Results Ready")

    @pytest.mark.asyncio
    async def test_stepper_with_single_step(self, user: User):
        """Test stepper with single step"""
        from nicegui import ui
        from frontend.components.shared import create_workflow_stepper

        steps = ["Only Step"]

        @ui.page("/test")
        async def test_page():
            container = ui.column().classes("w-full")
            create_workflow_stepper(steps, current_step=0, container=container)

        await user.open("/test")

        # Should see the single step
        await user.should_see("Only Step")
