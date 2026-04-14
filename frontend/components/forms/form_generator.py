"""
Dynamic Form Generator

This module provides the FormGenerator class for dynamically generating forms
based on TaskSchema definitions. It creates UI fields for inputs and parameters,
handles validation, and supports form submission callbacks.

The generator creates appropriate UI controls based on input types (directory,
file, text) and parameter types (ranged float/int, enum, text).

The main FormGenerator class orchestrates form creation, delegating field
building to form_field_builders and form handling to form_handlers.
"""

import logging
from nicegui import ui
from typing import Dict, Callable, Optional, Union
from pathlib import Path
import sys

# Add backend models to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from rb.api.models import TaskSchema

# Import field builders and handlers from separate modules
from frontend.components.forms.builders import (
    create_input_field,
    create_parameter_field,
)
from frontend.components.forms.form_handlers import handle_form_submit

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# (Legacy global registries and fallback cleanup removed — lifecycle is now owned by caller)


class FormGenerator:
    """
    Generate dynamic forms from TaskSchema.
    
    This class creates NiceGUI forms dynamically based on TaskSchema definitions.
    It supports various input types (directory, file, text) and parameter types
    (ranged values, enums, text). Forms include validation and submission handling.
    
    Usage:
        generator = FormGenerator()
        await generator.generate_form(
            schema=task_schema,
            container=ui.column(),
            initial_values={'inputs': {...}, 'parameters': {...}},
            onSubmit=handle_submit
        )
    
    Tips:
    - Forms are generated asynchronously to support async file browsing
    - Initial values should match the format: {'inputs': {...}, 'parameters': {...}}
    - Validation occurs on submission before calling onSubmit callback
    - Form widgets are stored internally for value retrieval
    """
    
    def __init__(self):
        """
        Initialize FormGenerator.
        
        Creates internal storage for form data, widgets, and validation errors.
        """
        logger.debug("Initializing FormGenerator")
        self.form_data = {}
        self.form_widgets = {}
        self.validation_errors = {}
    
    async def generate_form(
        self,
        schema: Union[TaskSchema, Dict],
        container,
        initial_values: Optional[Dict] = None,
        onSubmit: Optional[Callable] = None,
        onCancel: Optional[Callable] = None,
        compact: bool = False
    ):
        """
        Generate a dynamic form from TaskSchema.
        
        This method creates a complete form UI with input fields and parameters
        based on the provided schema. The form includes validation, initial values
        support, and a submission handler.
        
        Args:
            schema (Union[TaskSchema, Dict]): TaskSchema Pydantic model or dictionary.
                If dict, it will be converted to TaskSchema
            container: NiceGUI container element to add the form to (e.g., ui.column())
            initial_values (Optional[Dict]): Pre-filled form values with structure:
                {
                    'inputs': {key: {'path': value} or {'text': value}, ...},
                    'parameters': {key: value, ...}
                }
                Defaults to None (empty form)
            onSubmit (Optional[Callable]): Async callback function called when form is submitted.
                Receives validated form data dictionary. Defaults to None (no submission handler)
            compact (bool): Whether to use compact spacing and smaller layout. Defaults to False
        
        Returns:
            None: Form is added directly to the container
        
        Examples:
            >>> generator = FormGenerator()
            >>> await generator.generate_form(
            ...     schema=task_schema,
            ...     container=my_container,
            ...     initial_values={'inputs': {'input_dir': {'path': '/tmp'}}, 'parameters': {}},
            ...     onSubmit=handle_submit
            ... )
        
        Tips:
        - Schema can be a dict (converted automatically) or TaskSchema model
        - Initial values should match the form data structure
        - Form submission triggers validation before calling onSubmit
        - The form includes a Cancel button that clears the container
        - Input fields are created asynchronously to support file browsing
        """
        logger.info("Generating dynamic form from TaskSchema")
        logger.debug("Schema type: %s, initial_values provided: %s", type(schema).__name__, initial_values is not None)
        
        # Convert dict to TaskSchema if needed
        if isinstance(schema, dict):
            logger.debug("Converting dictionary schema to TaskSchema")
            schema = dict(schema)
            # Normalize parameters: if dict keyed by param name, convert to list
            params = schema.get('parameters')
            if isinstance(params, dict):
                schema['parameters'] = [
                    {
                        'key': k,
                        'label': v.get('label', k.replace('_', ' ').title()),
                        'subtitle': v.get('subtitle', ''),
                        'value': v.get('value', v)  # v is descriptor if no nested 'value'
                    }
                    for k, v in params.items()
                ]
            task_schema = TaskSchema(**schema)
        else:
            task_schema = schema
        
        self.form_data = initial_values or {}
        self.form_widgets = {}
        self.validation_errors = {}
        
        
        with container:
            logger.debug("Creating form layout (border/chrome from caller when wrapped in ui.card)")
            # Use compact spacing if requested
            if compact:
                column_classes = 'w-full min-w-0 max-w-full p-3 space-y-2'
                header_classes = 'text-lg font-bold'
                section_classes = 'font-semibold text-base mt-2'
                button_row_classes = 'mt-3 gap-2'
            else:
                column_classes = 'w-full min-w-0 max-w-full p-6 space-y-4'
                header_classes = 'text-xl font-bold'
                section_classes = 'font-semibold text-lg mt-4'
                button_row_classes = 'mt-6 gap-2'

            with ui.column().classes(column_classes):
                ui.label('📋 Input Form').classes(header_classes)
                logger.debug("Form header added")

                # Generate input fields
                if task_schema.inputs:
                    logger.info("Generating %d input fields", len(task_schema.inputs))
                    ui.label('Inputs').classes(section_classes)
                    for input_schema in task_schema.inputs:
                        await create_input_field(
                            input_schema,
                            self.form_widgets,
                            self.form_data.get('inputs', {})
                        )
                    logger.debug("Input fields generated")

                # Generate parameter fields
                if task_schema.parameters:
                    logger.info("Generating %d parameter fields", len(task_schema.parameters))
                    ui.label('Parameters').classes(section_classes)
                    for param_schema in task_schema.parameters:
                        await create_parameter_field(
                            param_schema,
                            self.form_widgets,
                            self.form_data.get('parameters', {})
                        )
                    logger.debug("Parameter fields generated")

                # Submit button (extracted to component)
                logger.info("Creating form action buttons (via component)")
                try:
                    from frontend.components.forms.form_actions import render_form_actions

                    def _on_cancel():
                        """
                        Cancel handler: remove the entire form card (if possible) so any
                        tool-selection UI rendered alongside the form is also removed.
                        Falls back to clearing the inner container when parent deletion
                        is not possible.
                        """
                        logger.debug("Cancel handler invoked for container=%r", container)
                        # Prefer deleting the parent card (if this column is nested inside it)
                        parent = getattr(container, 'parent', None)

                        # Helper: walk ancestors to find and delete a related selection card attribute
                        def _scan_and_delete_related(start_element):
                            anc = start_element
                            while anc:
                                sel = getattr(anc, '_related_tool_selection_card', None)
                                if sel:
                                    try:
                                        logger.debug("Cancel: deleting related selection card %r found on %r", sel, anc)
                                        sel.delete()
                                    except (RuntimeError, AttributeError) as e:
                                        logger.debug("Failed to delete related selection card during cancel: %s", e)
                                    try:
                                        delattr(anc, '_related_tool_selection_card')
                                    except (AttributeError, TypeError):
                                        # attribute removal failed or not present, ignore
                                        logger.debug("Could not delete _related_tool_selection_card attribute on %r", anc)
                                    return True
                                anc = getattr(anc, 'parent', None)
                            return False

                        # Try container first, then its parent chain
                        try:
                            deleted = _scan_and_delete_related(container)
                            logger.debug("Cancel: related selection card deleted=%s", deleted)
                            if not deleted and parent:
                                parent_deleted = _scan_and_delete_related(parent)
                                logger.debug("Cancel: related selection card found on parent=%s", parent_deleted)
                        except (RuntimeError, AttributeError) as e:
                            logger.debug("Error scanning ancestors for related selection card: %s", e, exc_info=True)

                        # Prefer deleting the parent card (if this column is nested inside it)
                        if parent:
                            try:
                                parent.delete()
                                logger.debug("Cancel: parent element deleted=%r", parent)
                                return
                            except (RuntimeError, AttributeError) as e:
                                # Fall through to clearing the container
                                logger.debug("Cancel: failed to delete parent element: %s", e)

                        # Fallback: clear the provided container
                        try:
                            container.clear()
                            logger.debug("Cancel: container cleared=%r", container)
                        except RuntimeError:
                            logger.debug("Container clear failed during cancel (client deleted)")
                        # Aggressive cleanup: clear any globally registered selection cards as a last resort
                        try:
                            from frontend.components.results.tool_selection_card import clear_active_tool_selection_cards
                            clear_active_tool_selection_cards()
                            logger.debug("Cancel: cleared active tool selection registry")
                        except (ImportError, AttributeError) as e:
                            logger.debug("Cancel: failed to clear active tool selection registry: %s", e)
                        if onCancel:
                            try:
                                onCancel()
                            except Exception as e:
                                logger.debug("onCancel callback failed: %s", e)

                    async def _on_submit():
                        if onSubmit:
                            return await handle_form_submit(
                                task_schema,
                                self.form_widgets,
                                onSubmit
                            )
                        return False

                    action_col = ui.column()
                    # Attach reference for form_actions to delete the outer container if needed.
                    try:
                        setattr(action_col, '_outer_form_container', container)
                    except (AttributeError, TypeError):
                        # highly unlikely, ignore
                        pass
                    render_form_actions(action_col, _on_cancel, _on_submit, compact=compact)
                except ImportError as e:
                    logger.warning("Failed to import form actions component: %s, falling back", e)
                    # Fallback inline
                    with ui.row().classes(button_row_classes):
                        ui.space()
                        def _fallback_cancel():
                            try:
                                container.clear()
                            except RuntimeError:
                                logger.debug("Fallback cancel failed: container already deleted")

                        ui.button(
                            'Cancel',
                            on_click=_fallback_cancel
                        ).classes('bg-gray-300')
                            
                        import asyncio
                        ui.button(
                            '▶ Submit Job',
                            on_click=lambda: asyncio.create_task(handle_form_submit(
                                task_schema,
                                self.form_widgets,
                                onSubmit
                            )) if onSubmit else None
                        ).classes('bg-green-600 text-white')

                logger.info("Form generation completed successfully")