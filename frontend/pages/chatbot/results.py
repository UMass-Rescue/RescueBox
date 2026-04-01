"""
Chatbot Results

This module handles rendering of job results with modern UI components.
"""

import logging
from nicegui import ui
from typing import Optional, Any
from frontend.components.results import ResultsPreview
from frontend.pages.chatbot.constants import FormConfig

logger = logging.getLogger(__name__)


class ResultRenderer:
    """Handles rendering of job results with modern UI components."""

    @staticmethod
    def get_result_icon(result_type: str) -> str:
        """Get appropriate icon for result type."""
        return FormConfig.RESULT_ICONS.get(result_type, 'help')

    @staticmethod
    def get_result_title(result_type: str, count: int) -> str:
        """Get formatted title for result type."""
        template = FormConfig.RESULT_TITLES.get(result_type, f'Result ({count} items)')
        plural = 's' if count != 1 else ''
        return template.format(count=count, plural=plural)

    @staticmethod
    def get_result_count(root: dict) -> int:
        """Get the count of items in the result."""
        result_type = root.get('output_type', '')

        if result_type == 'batchtext':
            return len(root.get('texts', []))
        elif result_type == 'batchfile':
            return len(root.get('files', []))
        else:
            return 1

    @staticmethod
    def create_success_header(
        job_id: Optional[str] = None,
        *,
        pipeline_intermediate: bool = False,
        pipeline_completed_step: Optional[int] = None,
        pipeline_total_steps: Optional[int] = None,
    ):
        """Create the success header with icon and job info."""
        try:
            from frontend.components.results.success_header import render_success_header
            render_success_header(
                ui.column(),
                job_id,
                pipeline_intermediate=pipeline_intermediate,
                pipeline_completed_step=pipeline_completed_step,
                pipeline_total_steps=pipeline_total_steps,
            )
        except Exception:
            with ui.row().classes('items-center gap-3 mb-6'):
                ui.icon('celebration', size='2rem').classes('text-green-600')
                with ui.column():
                    if pipeline_intermediate and pipeline_completed_step and pipeline_total_steps:
                        ui.label('Job complete').classes('text-2xl font-bold text-green-800')
                        ui.label(
                            f'Step {pipeline_completed_step} of {pipeline_total_steps} finished'
                        ).classes('text-sm text-green-700')
                    else:
                        ui.label('Job Completed Successfully!').classes('text-2xl font-bold text-green-800')
                    if job_id:
                        ui.label(f'Job ID: {job_id}').classes('text-sm text-green-600 font-mono')

    @staticmethod
    def create_result_card(result_type: str, result_title: str, result_count: int, on_expand, job_id: Optional[str] = None, **kwargs):
        """Create the main result card with expand functionality."""
        try:
            from frontend.components.results.result_card import render_result_card
            render_result_card(ui.column(), result_type, result_title, result_count, on_expand, job_id=job_id)
        except Exception:
            # Fallback to inline behavior if component fails to load
            with ui.card().classes('bg-white border border-green-200 rounded-xl hover:shadow-lg transition-all duration-300 cursor-pointer group'):
                with ui.row().classes('p-4 items-center justify-between'):
                    with ui.column().classes('flex-1'):
                        with ui.row().classes('items-center gap-3'):
                            result_icon = ResultRenderer.get_result_icon(result_type)
                            ui.icon(result_icon, size='1.5rem').classes('text-green-600')
                            with ui.column():
                                ui.label(result_title).classes('font-semibold text-gray-800')
                                ui.label(f'{result_count} item{"s" if result_count != 1 else ""}').classes('text-sm text-gray-500')
                    expand_btn = ui.button('View Details', icon='expand_more').classes('bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg transition-colors')
                    expand_btn.on_click(on_expand)
                    # Inline per-result View Job button (if job_id available)
                    if job_id:
                        ResultRenderer.render_view_job_button(job_id)
                    ui.button('', on_click=on_expand).classes('absolute inset-0 opacity-0')

    @staticmethod
    def render_view_job_button(job_id: str):
        """Render an inline 'View Job' button for a given job id."""
        try:
            ui.button('View Job', on_click=lambda jid=job_id: ui.navigate.to(f"/jobs/{jid}")).classes('ml-2 bg-blue-500 text-white')
        except Exception as e:
            logger.debug("Failed to render View Job button: %s", e)

    @staticmethod
    def show_error_message(message: str, details: str = None, debug_data: Any = None):
        """Show an error message with optional debug information."""
        try:
            from frontend.components.errors.error_display import render_error_message
            # render into a small inline column so callers can place it
            render_error_message(ui.column(), message, details=details, debug_data=debug_data)
        except Exception:
            # fallback inline
            ui.label(f'❌ {message}').classes('text-red-600 font-semibold')
            if details:
                ui.label(details).classes('text-gray-600 text-sm mt-2')
            if debug_data is not None:
                with ui.expansion('Details').classes('mt-4'):
                    ui.label('Debug Information:').classes('font-semibold mb-2')
                    ui.code(str(debug_data), language='json').classes('text-xs max-h-32 overflow-auto')

    @staticmethod
    async def show_result_popup(root: dict, result_type: str, title: str, response_dict: dict = None):
        """Show result details in a popup dialog."""
        logger.debug("Showing result popup for type: %s", result_type)

        # Validation
        if not root or not isinstance(root, dict):
            logger.error("Cannot show result popup: root is empty or invalid")
            ui.notify('Cannot display result details: invalid data format', type='negative')
            return

        if not root.get('output_type'):
            logger.error("Cannot show result popup: missing output_type in root")
            ui.notify('Cannot display result details: missing result type', type='negative')
            return

        try:
            from frontend.components.results.result_popup_component import show_result_popup_component
            # delegate to the component which creates its own dialog and opens it
            show_result_popup_component(root, title=title, response_dict=response_dict)
            return
        except Exception:
            # fallback to inline dialog if delegation fails
            with ui.dialog() as result_dialog:
                with ui.card().classes(FormConfig.RESULT_DETAIL_CLASSES):
                    # Header
                    with ui.row().classes('bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 items-center'):
                        ui.icon(ResultRenderer.get_result_icon(result_type), size='2rem').classes('mr-3')
                        ui.label(title).classes('text-xl font-bold flex-1')
                        ui.button(icon='close', on_click=result_dialog.close).classes('text-white hover:bg-white/20 rounded-full p-1')

                    # Content area with scrolling
                    with ui.scroll_area().classes('h-[60vh]'):
                        with ui.column().classes('p-6'):
                            ResultRenderer._render_result_content(root, result_type, response_dict)

            result_dialog.open()

    @staticmethod
    def _render_result_content(root: dict, result_type: str, response_dict: dict = None):
        """Render the actual result content in the popup."""
        # Validate data
        if not root or not isinstance(root, dict) or not root.get('output_type'):
            logger.error("Invalid root data for result popup: %s", root)
            ResultRenderer.show_error_message(
                'Unable to display result details: Invalid response format',
                'The server returned an incomplete or invalid response.',
                response_dict
            )
            return

        try:
            logger.debug("Attempting to render with ResultsPreview")
            response_data = {'root': root}
            logger.debug("Response data for ResultsPreview: %s", response_data)

            # Use the Result Popup component to show the detailed view
            from frontend.components.results.result_popup import show_result_popup
            show_result_popup(response_data['root'], title=result_type, response_dict=response_dict)
            logger.debug("Result popup shown successfully")
        except Exception as e:
            logger.error("Failed to render result details: %s", str(e))
            logger.error("Root data that caused error: %s", root)
            ResultRenderer.show_error_message(
                f'Error displaying result details: {str(e)}',
                'This may be due to an incompatible response format from the server.',
                {'root': root, 'full_response': response_dict}
            )

    @staticmethod
    async def render_with_strategy(container: ui.element, root: dict, response_dict: dict = None) -> None:
        """
        Render results using the strategy pattern for extensibility.

        Args:
            container: The UI container to render into
            root: The result data root
            response_dict: Optional full response dictionary
        """
        result_type = root.get('output_type', 'unknown')
        logger.debug("Rendering result with strategy pattern: %s", result_type)

        try:
            # Get the appropriate strategy
            strategy = result_strategy_factory.get_strategy(result_type)

            # Render using the strategy
            await strategy.render(container, root, response_dict)

        except Exception as e:
            logger.error("Strategy-based rendering failed: %s", str(e))
            # Fallback to error message
            with container:
                ResultRenderer.show_error_message(
                    f'Rendering failed: {str(e)}',
                    'Using strategy pattern rendering.',
                    {'root': root, 'error': str(e)}
                )


# Strategy Pattern Implementation for Extensible Result Rendering
# ============================================================================

from abc import ABC, abstractmethod
from typing import Protocol, Dict


class ResultRenderingStrategy(ABC):
    """
    Abstract base class for result rendering strategies.

    This defines the interface for different result rendering approaches,
    allowing extensible handling of various result types.
    """

    @abstractmethod
    def can_handle(self, result_type: str) -> bool:
        """
        Check if this strategy can handle the given result type.

        Args:
            result_type: The type of result to render

        Returns:
            True if this strategy can handle the result type
        """
        pass

    @abstractmethod
    async def render(self, container: ui.element, root: dict, response_dict: dict = None) -> None:
        """
        Render the result using this strategy.

        Args:
            container: The UI container to render into
            root: The result data root
            response_dict: Optional full response dictionary
        """
        pass


class TextResultStrategy(ResultRenderingStrategy):
    """Strategy for rendering text results."""

    def can_handle(self, result_type: str) -> bool:
        return result_type in ['text', 'batchtext']

    async def render(self, container: ui.element, root: dict, response_dict: dict = None) -> None:
        """Render text or batch text results."""
        with container:
            if root.get('output_type') == 'batchtext':
                # Use ResultsPreview for batch text rendering
                response_data = {'root': root}
                ResultsPreview.render(ui.column(), response_data)
            else:
                # Simple text rendering
                ui.label('📄 Text Result').classes('text-lg font-semibold mb-2')
                ui.label(root.get('value', 'No content')).classes('text-gray-700 whitespace-pre-wrap')


class FileResultStrategy(ResultRenderingStrategy):
    """Strategy for rendering file results."""

    def can_handle(self, result_type: str) -> bool:
        return result_type in ['file', 'batchfile']

    async def render(self, container: ui.element, root: dict, response_dict: dict = None) -> None:
        """Render file or batch file results."""
        with container:
            if root.get('output_type') == 'batchfile':
                # Use ResultsPreview for batch file rendering
                response_data = {'root': root}
                ResultsPreview.render(ui.column(), response_data)
            else:
                # Simple file rendering
                ui.label('📁 File Result').classes('text-lg font-semibold mb-2')
                ui.label(f"Path: {root.get('path', 'Unknown')}").classes('text-gray-700')


class ImageResultStrategy(ResultRenderingStrategy):
    """Strategy for rendering image results."""

    def can_handle(self, result_type: str) -> bool:
        return result_type == 'image'

    async def render(self, container: ui.element, root: dict, response_dict: dict = None) -> None:
        """Render image results."""
        with container:
            ui.label('🖼️ Image Result').classes('text-lg font-semibold mb-2')
            ui.label(f"Image: {root.get('filename', 'Unknown')}").classes('text-gray-700')


class DefaultResultStrategy(ResultRenderingStrategy):
    """Default strategy for unknown result types."""

    def can_handle(self, result_type: str) -> bool:
        return True  # Can handle any type as fallback

    async def render(self, container: ui.element, root: dict, response_dict: dict = None) -> None:
        """Render unknown result types with a generic display."""
        with container:
            ui.label('❓ Unknown Result Type').classes('text-lg font-semibold mb-2')
            ui.label(f"Type: {root.get('output_type', 'unknown')}").classes('text-gray-700')
            ui.code(str(root), language='json').classes('text-xs mt-2')


class ResultRenderingStrategyFactory:
    """
    Factory for creating result rendering strategies.

    This factory manages the available strategies and provides the appropriate
    strategy for a given result type.
    """

    def __init__(self):
        self._strategies = [
            TextResultStrategy(),
            FileResultStrategy(),
            ImageResultStrategy(),
            DefaultResultStrategy()  # Must be last as fallback
        ]

    def get_strategy(self, result_type: str) -> ResultRenderingStrategy:
        """
        Get the appropriate strategy for the result type.

        Args:
            result_type: The type of result to render

        Returns:
            The appropriate rendering strategy
        """
        for strategy in self._strategies:
            if strategy.can_handle(result_type):
                return strategy

        # This should never happen due to DefaultResultStrategy
        raise ValueError(f"No strategy found for result type: {result_type}")

    def register_strategy(self, strategy: ResultRenderingStrategy) -> None:
        """
        Register a new rendering strategy.

        Args:
            strategy: The strategy to register
        """
        # Insert before the default strategy
        self._strategies.insert(-1, strategy)


# Global strategy factory instance
result_strategy_factory = ResultRenderingStrategyFactory()
