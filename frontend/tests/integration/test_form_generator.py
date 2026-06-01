"""Integration tests for form generator using NiceGUI User fixture"""

import pytest
from nicegui.testing import User


class TestFormGenerator:
    """Tests for form generator component"""

    @pytest.mark.asyncio
    async def test_form_generator_creates_input_fields(
        self, user: User, sample_task_schema
    ):
        """Test form generator creates correct input fields"""
        from nicegui import ui
        from frontend.components.forms import FormGenerator

        @ui.page("/test")
        async def test_page():
            container = ui.column()
            form_gen = FormGenerator()
            await form_gen.generate_form(
                schema=sample_task_schema.model_dump(),
                container=container,
                endpoint="test/endpoint",
            )

        await user.open("/test")

        # Should see form fields
        await user.should_see("Input Directory")
        await user.should_see("Prompt")
        await user.should_see("Confidence")
        await user.should_see("Processing Mode")

    @pytest.mark.asyncio
    async def test_form_generator_submit_button(self, user: User, sample_task_schema):
        """Test form generator has submit button"""
        from nicegui import ui
        from frontend.components.forms import FormGenerator

        submit_called = False

        def test_submit(data):
            nonlocal submit_called
            submit_called = True

        @ui.page("/test")
        async def test_page():
            container = ui.column()
            form_gen = FormGenerator()
            await form_gen.generate_form(
                schema=sample_task_schema.model_dump(),
                container=container,
                onSubmit=test_submit,
                endpoint="test/endpoint",
            )

        await user.open("/test")

        await user.should_see("Submit")
        # Find and click submit button
        submit_button = user.find("Submit")
        assert submit_button is not None

        # Note: Actual submission would require filling form first
        # This tests that the button exists
