"""
Unit tests for workflow stepper component and step management.

This module tests the WorkflowStepper class that provides visual step-by-step
progress indication for multi-stage workflows in the RescueBox application.
The stepper component manages step navigation, visual state indication, and
provides a clear user interface for complex, multi-step processes.

The tests cover all major stepper functionality:
- Step initialization and configuration
- Navigation between steps (forward/backward)
- Boundary condition handling (first/last step limits)
- Visual styling and CSS class generation
- Completion state tracking
- Container integration for UI layout
- Convenience functions for stepper creation

These components are essential for guiding users through complex workflows
such as data analysis pipelines, forensic investigations, and multi-stage
processing tasks where clear progress indication is critical.
"""

import pytest
from unittest.mock import patch, MagicMock
from nicegui import ui

# Test constants for step names
STEP_1_NAME = 'Step 1'
STEP_2_NAME = 'Step 2'
STEP_3_NAME = 'Step 3'
STEP_4_NAME = 'Step 4'
STEP_5_NAME = 'Step 5'

STEPS_THREE = [STEP_1_NAME, STEP_2_NAME, STEP_3_NAME]
STEPS_TWO = [STEP_1_NAME, STEP_2_NAME]
STEPS_FIVE = [STEP_1_NAME, STEP_2_NAME, STEP_3_NAME, STEP_4_NAME, STEP_5_NAME]

# Step indices
FIRST_STEP_INDEX = 0
SECOND_STEP_INDEX = 1
THIRD_STEP_INDEX = 2
INVALID_NEGATIVE_INDEX = -1
INVALID_HIGH_INDEX = 3

# CSS class constants for visual styling
COMPLETED_STEP_BG_CLASS = 'bg-green-500'
CURRENT_STEP_BG_CLASS = 'rb-brand-step-current'
PENDING_STEP_BG_CLASS = 'bg-zinc-300'
COMPLETED_CURRENT_LABEL_CLASS = 'font-semibold'
PENDING_LABEL_CLASS = 'text-zinc-400'

# Warning messages
ALREADY_AT_LAST_STEP_WARNING = "Already at last step"
ALREADY_AT_FIRST_STEP_WARNING = "Already at first step"

# Step range error messages
STEP_INDEX_OUT_OF_RANGE_TEMPLATE = "Step index {index} out of range"


class TestWorkflowStepper:
    """Unit tests for WorkflowStepper class and step management functionality.

    This class validates the WorkflowStepper component that provides visual
    progress indication for multi-step workflows. Each test ensures proper
    step navigation, state management, and visual styling for a smooth
    user experience during complex operations.

    Stepper functionality tested:
    - Initialization with step lists and container integration
    - Step navigation (set_step, next_step, previous_step)
    - Boundary condition handling at workflow limits
    - Current step identification and naming
    - Completion state tracking
    - Visual styling with CSS classes for different step states
    - Convenience functions for stepper creation
    - Multi-step workflow support

    All tests validate that the stepper provides clear visual feedback
    and reliable navigation controls for users working through complex
    analytical workflows in RescueBox.
    """
    
    @patch('frontend.components.shared.stepper.ui.column')
    def test_stepper_initialization(self, mock_column):
        """Test stepper initialization with steps.

        Validates that the WorkflowStepper can be properly initialized
        with a list of step names and maintains correct internal state
        including step tracking and element management.
        """
        from frontend.components.shared.stepper import WorkflowStepper

        # Mock the container creation - ui.column() returns a mock container
        mock_container = MagicMock()
        mock_column.return_value = mock_container

        stepper = WorkflowStepper(STEPS_THREE, current_step=FIRST_STEP_INDEX)

        assert stepper.steps == STEPS_THREE
        assert stepper.current_step == FIRST_STEP_INDEX
        # In test mode with mocked UI, step_elements should be empty
        assert len(stepper.step_elements) == 0

    def test_stepper_with_container(self, mock_ui):
        """Test stepper initialization with container.

        Ensures that steppers can be properly integrated with UI containers
        for layout management, allowing flexible placement within the
        application's user interface structure.
        """
        from frontend.components.shared.stepper import WorkflowStepper

        container = MagicMock()
        stepper = WorkflowStepper(STEPS_TWO, current_step=FIRST_STEP_INDEX, container=container)

        assert stepper.container == container
        assert stepper.current_step == FIRST_STEP_INDEX
    
    def test_set_step_valid(self, mock_ui):
        """Test setting step to valid index.

        Validates that step navigation works correctly for valid step indices,
        allowing users to jump to specific steps in the workflow as needed
        for non-linear progress through complex processes.
        """
        from frontend.components.shared.stepper import WorkflowStepper

        # Mock the container creation
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container

        stepper = WorkflowStepper(STEPS_THREE, current_step=FIRST_STEP_INDEX)

        stepper.set_step(SECOND_STEP_INDEX)
        assert stepper.current_step == SECOND_STEP_INDEX

        stepper.set_step(THIRD_STEP_INDEX)
        assert stepper.current_step == THIRD_STEP_INDEX

    def test_set_step_invalid_index(self, mock_ui):
        """Test setting step to invalid index raises ValueError.

        Ensures that attempts to navigate to non-existent steps are properly
        rejected with clear error messages, preventing application crashes
        and providing user feedback about invalid navigation attempts.
        """
        from frontend.components.shared.stepper import WorkflowStepper

        # Mock the container creation
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container

        stepper = WorkflowStepper(STEPS_THREE, current_step=FIRST_STEP_INDEX)

        with pytest.raises(ValueError, match=STEP_INDEX_OUT_OF_RANGE_TEMPLATE.format(index=INVALID_NEGATIVE_INDEX)):
            stepper.set_step(INVALID_NEGATIVE_INDEX)

        with pytest.raises(ValueError, match=STEP_INDEX_OUT_OF_RANGE_TEMPLATE.format(index=INVALID_HIGH_INDEX)):
            stepper.set_step(INVALID_HIGH_INDEX)
    
    def test_next_step(self, mock_ui):
        """Test moving to next step"""
        from frontend.components.shared.stepper import WorkflowStepper

        # Mock the container creation
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container

        steps = ['Step 1', 'Step 2', 'Step 3']
        stepper = WorkflowStepper(steps, current_step=0)
        
        stepper.next_step()
        assert stepper.current_step == 1
        
        stepper.next_step()
        assert stepper.current_step == 2
    
    def test_next_step_at_last_step(self, mock_ui):
        """Test next_step when already at last step.

        Validates that attempting to advance beyond the final step is handled
        gracefully with appropriate logging, preventing navigation errors and
        maintaining workflow stability at completion boundaries.
        """
        from frontend.components.shared.stepper import WorkflowStepper

        # Mock the container creation
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container

        stepper = WorkflowStepper(STEPS_TWO, current_step=SECOND_STEP_INDEX)

        with patch('frontend.components.shared.stepper.logger') as mock_logger:
            stepper.next_step()
            # Should stay at last step
            assert stepper.current_step == SECOND_STEP_INDEX
            mock_logger.warning.assert_called_once()
            assert ALREADY_AT_LAST_STEP_WARNING in mock_logger.warning.call_args[0][0]
    
    def test_previous_step(self, mock_ui):
        """Test moving to previous step"""
        from frontend.components.shared.stepper import WorkflowStepper

        # Mock the container creation
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container

        steps = ['Step 1', 'Step 2', 'Step 3']
        stepper = WorkflowStepper(steps, current_step=2)
        
        stepper.previous_step()
        assert stepper.current_step == 1
        
        stepper.previous_step()
        assert stepper.current_step == 0
    
    def test_previous_step_at_first_step(self, mock_ui):
        """Test previous_step when already at first step"""
        from frontend.components.shared.stepper import WorkflowStepper
        from unittest.mock import patch

        # Mock the container creation
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container

        steps = ['Step 1', 'Step 2']
        stepper = WorkflowStepper(steps, current_step=0)
        
        with patch('frontend.components.shared.stepper.logger') as mock_logger:
            stepper.previous_step()
            # Should stay at first step
            assert stepper.current_step == 0
            mock_logger.warning.assert_called_once()
            assert "Already at first step" in mock_logger.warning.call_args[0][0]
    
    def test_get_current_step_name(self, mock_ui):
        """Test getting current step name"""
        from frontend.components.shared.stepper import WorkflowStepper

        # Mock the container creation
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container

        steps = ['Step 1', 'Step 2', 'Step 3']
        stepper = WorkflowStepper(steps, current_step=1)
        
        assert stepper.get_current_step_name() == 'Step 2'
    
    def test_is_complete(self, mock_ui):
        """Test is_complete method"""
        from frontend.components.shared.stepper import WorkflowStepper

        # Mock the container creation
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container

        steps = ['Step 1', 'Step 2', 'Step 3']
        stepper = WorkflowStepper(steps, current_step=0)
        
        assert stepper.is_complete() is False
        
        stepper.set_step(1)
        assert stepper.is_complete() is False
        
        stepper.set_step(2)  # Last step (index 2 of 3 steps)
        assert stepper.is_complete() is True
    
    def test_create_workflow_stepper(self, mock_ui):
        """Test create_workflow_stepper convenience function"""
        from frontend.components.shared.stepper import (
            create_workflow_stepper,
            WorkflowStepper
        )

        # Mock the container creation
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container

        steps = ['Step 1', 'Step 2']
        stepper = create_workflow_stepper(steps, current_step=1)
        
        assert isinstance(stepper, WorkflowStepper)
        assert stepper.current_step == 1
        assert stepper.steps == steps
    
    def test_stepper_multiple_steps(self, mock_ui):
        """Test stepper with many steps"""
        from frontend.components.shared.stepper import WorkflowStepper

        # Mock the container creation
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container

        steps = ['Step 1', 'Step 2', 'Step 3', 'Step 4', 'Step 5']
        stepper = WorkflowStepper(steps, current_step=0)
        
        # Progress through all steps
        for i in range(len(steps)):
            stepper.set_step(i)
            assert stepper.current_step == i
            assert stepper.get_current_step_name() == steps[i]
        
        # Should be complete at last step
        assert stepper.is_complete() is True
    
    def test_stepper_circle_classes(self, mock_ui):
        """Test circle class generation"""
        from frontend.components.shared.stepper import WorkflowStepper

        # Mock the container creation
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container

        steps = ['Step 1', 'Step 2', 'Step 3']
        stepper = WorkflowStepper(steps, current_step=1)
        
        # Completed step (index 0)
        assert 'bg-green-500' in stepper._get_circle_classes(0)
        
        # Current step (index 1)
        assert 'rb-brand-step-current' in stepper._get_circle_classes(1)
        
        # Pending step (index 2)
        assert 'bg-zinc-300' in stepper._get_circle_classes(2)
    
    def test_stepper_label_classes(self, mock_ui):
        """Test label class generation"""
        from frontend.components.shared.stepper import WorkflowStepper

        # Mock the container creation
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container

        steps = ['Step 1', 'Step 2', 'Step 3']
        stepper = WorkflowStepper(steps, current_step=1)
        
        # Completed/current step labels
        assert 'font-semibold' in stepper._get_label_classes(0)
        assert 'font-semibold' in stepper._get_label_classes(1)
        
        # Pending step label
        assert 'text-zinc-400' in stepper._get_label_classes(2)
    
    def test_stepper_line_classes(self, mock_ui):
        """Test connector line class generation"""
        from frontend.components.shared.stepper import WorkflowStepper

        # Mock the container creation
        mock_container = MagicMock()
        mock_ui.column.return_value = mock_container

        steps = ['Step 1', 'Step 2', 'Step 3']
        stepper = WorkflowStepper(steps, current_step=1)
        
        # Completed path
        assert 'bg-green-500' in stepper._get_line_classes(0)
        
        # Pending path
        assert 'bg-zinc-300' in stepper._get_line_classes(1)

