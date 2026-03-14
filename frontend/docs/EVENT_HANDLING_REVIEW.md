# NiceGUI Event Handling Review

## Overview

This document reviews event handling across the RescueBox frontend codebase, comparing current implementation with NiceGUI's event capabilities as documented at [NiceGUI Action Events](https://nicegui.io/documentation/section_action_events).

## Current Event Usage Summary

### ✅ Events Currently Implemented

#### Chat Area (`frontend/pages/chatbot/`)
- **`on_click`**: Send button, History button, New Conversation button, Quick command buttons (Tools, Analyze, Help), Attach button
- **`keydown`**: Enter key handling for sending messages (Shift+Enter for new line)
- **`on_change`**: Search input in chat history panel

#### Jobs Area (`frontend/pages/jobs/`)
- **`on_click`**: Refresh button, View button, Cancel button, Delete button
- Navigation: Model details links, Job details links

#### Results Area (`frontend/components/results/`)
- **`on_click`**: Open File button, Open Folder button, Image clicks
- **`rowClick`**: Table row clicks for opening files/folders
- **`on('update:modelValue')`**: Real-time search input updates in searchable file lists
- **`on('blur')`**: Search input blur event

#### Forms Area (`frontend/components/forms/`)
- **`on_click`**: Browse buttons (directory/file), Submit button, Cancel button
- **`on_submit`**: Form submission handlers (via FormGenerator)
- **`on_change`**: File browser drive selection (Windows)

#### Model Components (`frontend/components/models/`)
- **`on_click`**: Inspect button, Run button, Connect button

#### Chat History (`frontend/components/chat/`)
- **`on_click`**: Refresh button, View conversation, Load conversation, Re-run tool call, Close button
- **`on_change`**: Search conversations filter

## NiceGUI Event Types Available

According to NiceGUI documentation, the following events are available:

1. **Mouse Events**:
   - `on_click` - Click events (buttons, cards, etc.)
   - `on_mousedown`, `on_mouseup`, `on_mousemove`
   - `on_mouseenter`, `on_mouseleave` (hover)

2. **Keyboard Events**:
   - `on_keydown`, `on_keyup`, `on_keypress`
   - Special handling for Enter, Escape, etc.

3. **Input Events**:
   - `on_change` - Value changes (inputs, selects, sliders)
   - `on_input` - Input while typing
   - `on_update:modelValue` - Reactive value updates

4. **Focus Events**:
   - `on_focus` - Element gains focus
   - `on_blur` - Element loses focus

5. **Form Events**:
   - `on_submit` - Form submission

6. **Table Events**:
   - `on('rowClick')` - Row click
   - `on('rowDbClick')` - Row double-click

7. **Custom Events**:
   - `.on('eventName', handler)` - Custom event handling

## Gap Analysis

### ❌ Missing Events That Could Improve UX

#### 1. Form Input Validation Events

**Current State**: Form validation only occurs on submission
**Missing**: Real-time validation feedback

**Recommendation**: Add `on_input` or `on_change` handlers for validation feedback

**Areas**:
- `frontend/components/forms/form_field_builders.py`
  - Input fields (directory, file, text) - no validation on change
  - Parameter fields (sliders, selects) - no live preview/validation

**Example Improvement**:
```python
# Current: No validation feedback
dir_input = ui.input(label='Directory path', ...)

# Improved: Real-time validation
dir_input.on('update:modelValue', lambda e: validate_and_show_error(dir_input, e.args))
```

#### 2. Search Input Debouncing

**Current State**: Search updates on every keystroke (could be improved with debouncing)
**Implemented**: ✅ Real-time search in `text_renderers.py` (searchable file list)
**Missing**: Debouncing to reduce updates during rapid typing

**Example Improvement**:
```python
# Add debouncing for better performance
import asyncio
search_debounce_task = None

def on_search_change(e):
    global search_debounce_task
    if search_debounce_task:
        search_debounce_task.cancel()
    search_debounce_task = asyncio.create_task(debounced_update(e.args))
```

#### 3. Keyboard Shortcuts

**Current State**: Only Enter key for sending messages
**Missing**: Additional keyboard shortcuts for common actions

**Recommendations**:
- `Ctrl+K` or `/` - Focus search/command input
- `Esc` - Close dialogs, cancel operations
- `Ctrl+Enter` - Submit forms
- Arrow keys - Navigate lists, tables

**Areas**:
- Chat interface - could add more shortcuts
- Job list - keyboard navigation
- Results tables - keyboard navigation

#### 4. Double-Click Events

**Current State**: Single click for table rows
**Missing**: Double-click for common actions (e.g., double-click file to open, double-click job to view details)

**Areas**:
- `frontend/components/results/table_helpers.py` - Could add `rowDbClick` handler
- `frontend/pages/jobs/jobs.py` - Double-click job row to view details

**Example**:
```python
table.on('rowDbClick', lambda e: open_file_from_row(e.args[1]))
```

#### 5. Hover Events

**Current State**: No hover effects or tooltips for interactive elements
**Missing**: Hover feedback for better UX

**Recommendations**:
- Tooltips on buttons (what action they perform)
- Hover effects on clickable rows/items
- Preview on hover (e.g., image thumbnails, file info)

**Areas**:
- All interactive elements could benefit from hover feedback

#### 6. Focus Management

**Current State**: Limited focus handling
**Missing**: Focus management for better keyboard navigation

**Recommendations**:
- Auto-focus search inputs when dialogs open
- Focus management during form submission
- Focus trap in dialogs (focus stays within dialog)

**Areas**:
- `frontend/components/chat/chat_history_panel.py` - Search input should auto-focus
- File browser dialogs - Focus management
- Form dialogs - Focus trap

#### 7. Input Field Validation Feedback

**Current State**: Validation errors shown on submission only
**Missing**: Real-time validation with visual feedback

**Recommendations**:
- Show error messages as user types
- Visual indicators (red border) for invalid fields
- Success indicators for valid fields

**Areas**:
- `frontend/components/forms/form_field_builders.py` - All input types

#### 8. Slider Value Preview

**Current State**: Sliders show value label (✅ implemented)
**Missing**: Could add tooltip or preview during drag

**Areas**:
- `frontend/components/forms/form_field_builders.py` - RangedFloat/IntParameterDescriptor

#### 9. Drag and Drop Events

**Current State**: File selection only via browse button
**Missing**: Drag-and-drop file/directory selection

**Recommendations**:
- Add drag-and-drop zones for file/directory inputs
- Visual feedback during drag

**Areas**:
- `frontend/components/forms/form_field_builders.py` - File and directory inputs

#### 10. Table Column Sorting Events

**Current State**: ✅ Tables are sortable (NiceGUI handles this internally)
**Status**: Adequate - sorting is built into NiceGUI tables

#### 11. Dialog Events

**Current State**: Dialogs open/close via buttons
**Missing**: Escape key to close, click outside to close

**Areas**:
- History dialog
- File browser dialogs
- Form dialogs

#### 12. Image Preview on Hover

**Current State**: Images clickable to open
**Missing**: Hover preview or zoom

**Areas**:
- `frontend/components/results/file_renderers.py` - Image rendering

## Priority Recommendations

### High Priority (Improves Core UX)

1. **Real-time Form Validation** (Forms)
   - Add `on_input` handlers for validation feedback
   - Show errors as user types
   - Visual indicators (red border for invalid)

2. **Keyboard Shortcuts** (Chat, Jobs, Results)
   - Escape key to close dialogs
   - Ctrl+K for search/command
   - Arrow keys for navigation

3. **Focus Management** (All dialogs)
   - Auto-focus inputs when dialogs open
   - Focus trap in dialogs

### Medium Priority (Enhances Usability)

4. **Double-Click Actions** (Tables)
   - Double-click file to open
   - Double-click job to view details

5. **Hover Effects** (All interactive elements)
   - Tooltips on buttons
   - Hover feedback on rows
   - Image preview on hover

6. **Search Debouncing** (Search inputs)
   - Reduce API calls during typing
   - Better performance

### Low Priority (Nice to Have)

7. **Drag and Drop** (File inputs)
   - Drag files/directories into inputs

8. **Enhanced Slider Feedback** (Parameter inputs)
   - Tooltip during drag

## Implementation Examples

### Example 1: Real-time Form Validation

```python
def create_validated_input_field(field_id, schema, initial_value):
    """Create input field with real-time validation"""
    input_field = ui.input(
        label=schema.label,
        value=initial_value
    )
    
    error_label = ui.label('').classes('text-red-600 text-xs')
    error_label.visible = False
    
    def validate_on_change(e):
        value = e.args if isinstance(e.args, str) else input_field.value
        try:
            # Validate value
            validate_input_value(value, schema)
            error_label.visible = False
            input_field.classes('border-green-500', remove='border-red-500')
        except ValidationError as err:
            error_label.text = str(err)
            error_label.visible = True
            input_field.classes('border-red-500', remove='border-green-500')
    
    input_field.on('update:modelValue', validate_on_change)
    return input_field, error_label
```

### Example 2: Keyboard Shortcuts

```python
def setup_keyboard_shortcuts():
    """Setup global keyboard shortcuts"""
    def handle_keydown(e):
        if e.args.key == 'Escape':
            # Close open dialogs
            close_all_dialogs()
        elif e.args.ctrl and e.args.key == 'k':
            # Focus search
            focus_search_input()
    
    ui.context.client.content.on('keydown', handle_keydown)
```

### Example 3: Double-Click Handler

```python
def create_table_with_double_click(columns, rows, on_single_click, on_double_click):
    """Create table with both single and double-click handlers"""
    table = ui.table(columns=columns, rows=rows)
    
    table.on('rowClick', on_single_click)
    table.on('rowDbClick', on_double_click)
    
    return table
```

### Example 4: Auto-Focus Input

```python
def create_dialog_with_auto_focus():
    """Create dialog with auto-focused input"""
    with ui.dialog() as dialog:
        search_input = ui.input(placeholder='Search...')
        # Auto-focus after dialog opens
        dialog.on('show', lambda: search_input.focus())
        dialog.open()
```

## Current Implementation Quality

### ✅ Well Implemented

1. **Basic Click Events**: Comprehensive `on_click` usage throughout
2. **Keyboard Events**: Enter key handling in chat
3. **Table Events**: Row click handling
4. **Reactive Updates**: Search with `update:modelValue`

### ⚠️ Needs Improvement

1. **Form Validation**: No real-time feedback
2. **Keyboard Shortcuts**: Limited keyboard support
3. **Focus Management**: No auto-focus or focus trapping
4. **Hover Effects**: No hover feedback
5. **Double-Click**: Missing double-click actions

### ❌ Missing

1. **Drag and Drop**: Not implemented
2. **Input Debouncing**: Could improve search performance
3. **Enhanced Validation**: No visual validation feedback
4. **Dialog Keyboard Handling**: Escape key not handled

## Conclusion

The frontend has **good basic event coverage** with comprehensive `on_click` handlers and some keyboard support. However, there are opportunities to enhance the user experience with:

1. **Real-time form validation** for better feedback
2. **Additional keyboard shortcuts** for power users
3. **Focus management** for better accessibility
4. **Hover effects and tooltips** for better discoverability
5. **Double-click actions** for faster workflows

**Overall Assessment**: **Adequate** for core functionality, but could be enhanced with the priority improvements listed above.

## Related Documentation

- [NiceGUI Action Events Documentation](https://nicegui.io/documentation/section_action_events)
- See `ERROR_HANDLING_REVIEW.md` for error handling patterns
- See `COMPLEXITY_COMPARISON.md` for architecture overview

