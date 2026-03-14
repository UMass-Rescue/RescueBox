# Stepper and Notification Components

This document describes the enhanced notification system and workflow stepper component for improving user experience in the RescueBox Desktop frontend.

## Overview

The frontend now includes:
1. **Enhanced Notification System** - Better styled, positioned notifications
2. **Workflow Stepper Component** - Visual progress indicator for multi-step workflows

## Enhanced Notifications

### Location
`frontend/components/shared/notifications.py`

### Functions

#### `notify_success(message, duration=3.0, position='top', close_button=True)`
Show success notification with green styling.

```python
from frontend.components.shared import notify_success
notify_success("Job submitted successfully")
```

#### `notify_error(message, duration=5.0, position='top', close_button=True)`
Show error notification with red styling.

```python
from frontend.components.shared import notify_error
notify_error("Failed to submit job")
```

#### `notify_info(message, duration=3.0, position='top', close_button=True)`
Show info notification with blue styling.

```python
from frontend.components.shared import notify_info
notify_info("Processing your request...")
```

#### `notify_warning(message, duration=4.0, position='top', close_button=True)`
Show warning notification with orange/yellow styling.

```python
from frontend.components.shared import notify_warning
notify_warning("Please check your input")
```

### Integration

The enhanced notifications are automatically integrated into `frontend/utils/error_handling.py`:
- `show_error_to_user()` - Uses `notify_error()` or `notify_warning()`
- `show_success_to_user()` - Uses `notify_success()`
- Falls back to `ui.notify()` if enhanced notifications are unavailable

### Benefits

- **Consistent Styling**: All notifications use the same styling across the app
- **Better Positioning**: Configurable position (top, bottom, left, right)
- **Persistent Option**: Can set duration to 0 for persistent notifications
- **User Preferences**: Can be extended to respect user preferences (see `frontend/utils/user_preferences.py`)

## Workflow Stepper Component

### Location
`frontend/components/shared/stepper.py`

### Purpose

The `WorkflowStepper` component provides a visual progress indicator for multi-step workflows, helping users understand:
- Where they are in the process
- What steps remain
- What steps have been completed

### Usage

#### Basic Usage

```python
from frontend.components.shared import create_workflow_stepper

# Define workflow steps
steps = ['Select Tool', 'Fill Form', 'Submit', 'View Results']

# Create stepper
stepper = create_workflow_stepper(steps, current_step=0)

# Update stepper as workflow progresses
stepper.next_step()  # Move to next step
stepper.set_step(2)  # Jump to specific step
stepper.previous_step()  # Go back one step
```

#### Chatbot Workflow Example

```python
from frontend.components.shared import WorkflowStepper

# Define chatbot workflow steps
CHATBOT_STEPS = [
    'Message Sent',
    'Tool Selected',
    'Form Ready',
    'Submitting',
    'Results Ready'
]

# Create stepper in UI
with ui.column():
    stepper_container = ui.column()
    stepper = WorkflowStepper(CHATBOT_STEPS, current_step=0, container=stepper_container)
    
    # As workflow progresses:
    stepper.set_step(1)  # After tool is selected
    stepper.set_step(2)  # After form is loaded
    stepper.set_step(3)  # After form is submitted
    stepper.set_step(4)  # After results are ready
```

### API

#### `WorkflowStepper(steps, current_step=0, container=None)`

**Parameters:**
- `steps` (List[str]): List of step names
- `current_step` (int): Initial step index (0-based)
- `container` (Optional[ui.element]): Container to render into

**Methods:**
- `set_step(step_index)` - Set current step by index
- `next_step()` - Move to next step
- `previous_step()` - Move to previous step
- `get_current_step_name()` - Get name of current step
- `is_complete()` - Check if all steps are complete

### Visual Design

The stepper displays:
- **Completed steps**: Green circle with checkmark
- **Current step**: Blue circle with step number
- **Pending steps**: Gray circle with step number
- **Connector lines**: Green for completed path, gray for pending

### Use Cases

1. **Chatbot Workflow**: Show progress through message → tool → form → submission → results
2. **Form Submission**: Show validation → submission → processing → results
3. **Job Creation**: Show form → validation → submission → processing → completion
4. **Multi-step Wizards**: Any multi-step process that benefits from visual progress

### Benefits

- **Better UX**: Users understand where they are in the process
- **Reduced Confusion**: Clear visual indication of progress
- **Professional Appearance**: Polished, modern UI component
- **Accessibility**: Visual progress indicator helps users with cognitive load

## Integration Examples

### Chatbot Integration

```python
# In chatbot.py
from frontend.components.shared import create_workflow_stepper, notify_info

class ChatbotPage:
    def __init__(self):
        self.stepper = None
        self.workflow_steps = ['Message Sent', 'Tool Selected', 'Form Ready', 'Submitting', 'Results Ready']
    
    async def render(self):
        # Create stepper in header
        with ui.row().classes('w-full bg-gray-100 p-2'):
            stepper_container = ui.column().classes('w-full')
            self.stepper = create_workflow_stepper(
                self.workflow_steps,
                current_step=0,
                container=stepper_container
            )
        
        # ... rest of UI
    
    async def send_message(self):
        # Step 1: Message sent
        self.stepper.set_step(0)
        notify_info("Processing your message...")
        
        # ... process message
    
    async def load_and_show_form(self, endpoint, arguments):
        # Step 2: Tool selected
        self.stepper.set_step(1)
        notify_info(f"Selected tool: {endpoint}")
        
        # Step 3: Form ready
        await load_form(...)
        self.stepper.set_step(2)
        
        # ... show form
    
    async def handle_form_submit(self, ...):
        # Step 4: Submitting
        self.stepper.set_step(3)
        notify_info("Submitting job...")
        
        # ... submit job
        
        # Step 5: Results ready
        self.stepper.set_step(4)
        notify_success("Job completed successfully!")
```

## Best Practices

1. **Use steppers for multi-step workflows** (3+ steps)
2. **Update stepper at each major milestone**
3. **Combine stepper with notifications** for better feedback
4. **Keep step names concise** (2-3 words)
5. **Use notifications for immediate feedback** (success, error, info)
6. **Use stepper for progress tracking** (where am I in the process)

## Future Enhancements

Potential improvements:
- **User preferences**: Allow users to disable/enable notifications
- **Stepper animations**: Smooth transitions between steps
- **Step tooltips**: Additional information on hover
- **Keyboard navigation**: Navigate steps with keyboard
- **Progress percentage**: Show "Step 2 of 5" text
- **Step descriptions**: Additional context for each step

## References

- NiceGUI Documentation: https://nicegui.io/documentation/section_page_layout
- NiceGUI Notifications: https://nicegui.io/documentation/section_features/notifications

