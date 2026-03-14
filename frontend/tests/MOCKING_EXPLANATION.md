# Understanding MagicMock and Context Manager Protocol in Tests

## What is MagicMock?

`MagicMock` is a Python testing utility from `unittest.mock` that creates mock objects that automatically create attributes and methods as you access them. This is useful for testing when you need to mock complex objects without manually defining every attribute.

### Basic MagicMock Example

```python
from unittest.mock import MagicMock

# Create a mock object
mock_obj = MagicMock()

# Access any attribute - it's automatically created!
mock_obj.some_attribute  # Returns another MagicMock
mock_obj.some_method()    # Returns another MagicMock
mock_obj.another_method(1, 2, 3)  # Works with any arguments

# You can set return values
mock_obj.calculate.return_value = 42
assert mock_obj.calculate() == 42

# You can verify calls were made
mock_obj.calculate.assert_called_once()
```

## The Problem: Context Manager Protocol

### What is a Context Manager?

A context manager is an object that can be used with Python's `with` statement:

```python
with some_object:
    # do something
```

For an object to work as a context manager, it must implement two special methods:
- `__enter__()` - Called when entering the `with` block
- `__exit__(exc_type, exc_val, exc_tb)` - Called when exiting the `with` block

### Example from Our Code

In `frontend/components/results/file_renderers.py`:

```python
def render_file(container, response: FileResponse):
    try:
        # ... code ...
        with container:  # <-- This requires container to be a context manager
            with ui.card():
                # ... render UI ...
    except Exception as e:
        with container:  # <-- Also used here in error handler
            ui.label(f'Error displaying file: {str(e)}')
```

The `container` parameter is expected to be a context manager that can be used with `with container:`.

## The Problem with MagicMock as Context Manager

### What Happens When You Try This:

```python
from unittest.mock import MagicMock

container = MagicMock()

# This will FAIL with: TypeError: 'MagicMock' object does not support the context manager protocol
with container:
    print("This won't work!")
```

### Why It Fails

By default, `MagicMock` doesn't implement `__enter__` and `__exit__` in a way that makes it a proper context manager. When Python tries to use it with `with`, it checks if the object supports the context manager protocol, and `MagicMock` fails this check.

## Solutions

### Solution 1: Manually Configure MagicMock (Simple Cases)

For simple cases where you just need the context manager to work:

```python
from unittest.mock import MagicMock

container = MagicMock()
container.__enter__ = MagicMock(return_value=container)
container.__exit__ = MagicMock(return_value=False)

# Now this works!
with container:
    print("This works!")
```

**Example from our test code** (`test_render_file_nonexistent_image`):

```python
container = MagicMock()
container.__enter__ = Mock(return_value=container)
container.__exit__ = Mock(return_value=False)

# Now container can be used with 'with' statement
with container:
    # ... test code ...
```

### Solution 2: Create a Real Context Manager Class (Complex Cases)

For cases where you need more control (like raising exceptions on first use):

```python
class ExceptionRaisingContainer:
    def __init__(self):
        self.enter_count = 0
    
    def __enter__(self):
        self.enter_count += 1
        if self.enter_count == 1:
            # First call raises exception (simulates error)
            raise Exception("Rendering error")
        # Second call succeeds (allows error handler to work)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Handle any exceptions
        return None  # Don't suppress exceptions

container = ExceptionRaisingContainer()

# First use raises exception
try:
    with container:
        print("This will fail")
except Exception as e:
    print(f"Caught: {e}")

# Second use succeeds
with container:
    print("This works!")
```

**Example from our test code** (`test_render_file_generic_exception`):

```python
class ExceptionRaisingContainer:
    def __init__(self):
        self.enter_count = 0
    
    def __enter__(self):
        self.enter_count += 1
        if self.enter_count == 1:
            # First call (in main try block) raises exception
            raise Exception("Rendering error")
        # Second call (in except block) succeeds
        return self
    
    def __exit__(self, *args):
        return None

container = ExceptionRaisingContainer()

# This tests that the function catches exceptions and shows error
render_file(container, response)
```

## Real-World Example from Our Tests

### The Problem We Encountered

In `test_render_file_generic_exception`, we initially tried:

```python
# ❌ THIS DOESN'T WORK
container = MagicMock()
container.__enter__ = Mock(side_effect=Exception("Rendering error"))

# When render_file tries: with container:
# TypeError: 'Mock' object does not support the context manager protocol
```

### Why It Failed

The issue was that when `render_file` does:

```python
with container:  # Line 63
    # ... code ...
```

Python checks if `container` supports the context manager protocol. Even though we set `__enter__`, the way we set it up caused issues because:

1. The exception was raised during the `with` statement itself
2. The error handler also tries `with container:` (line 96)
3. The mock wasn't properly configured to handle both calls

### The Solution

We created a real context manager class that:

1. **Raises exception on first use** - Simulates the error in the main code
2. **Succeeds on second use** - Allows the error handler to display the error message
3. **Properly implements the protocol** - Works correctly with `with` statements

```python
# ✅ THIS WORKS
class ExceptionRaisingContainer:
    def __init__(self):
        self.enter_count = 0
    
    def __enter__(self):
        self.enter_count += 1
        if self.enter_count == 1:
            raise Exception("Rendering error")
        return self
    
    def __exit__(self, *args):
        return None

container = ExceptionRaisingContainer()
render_file(container, response)  # Works correctly!
```

## Key Takeaways

1. **MagicMock is great** for simple mocking, but needs configuration for context managers
2. **Context manager protocol** requires `__enter__` and `__exit__` methods
3. **For complex scenarios** (like testing exception handling), a real class is often clearer
4. **Always test your mocks** - if something doesn't work with `with`, the mock isn't set up correctly

## Common Patterns

### Pattern 1: Simple Context Manager Mock

```python
container = MagicMock()
container.__enter__ = Mock(return_value=container)
container.__exit__ = Mock(return_value=False)
```

### Pattern 2: Context Manager That Tracks Usage

```python
class TrackingContainer:
    def __init__(self):
        self.entered = False
    
    def __enter__(self):
        self.entered = True
        return self
    
    def __exit__(self, *args):
        return None
```

### Pattern 3: Context Manager That Raises Exception

```python
class ExceptionContainer:
    def __enter__(self):
        raise ValueError("Test error")
    
    def __exit__(self, *args):
        return None
```

## Summary

- **MagicMock** automatically creates attributes/methods but needs help for context managers
- **Context manager protocol** = `__enter__()` and `__exit__()` methods
- **Simple cases**: Configure MagicMock's `__enter__` and `__exit__`
- **Complex cases**: Create a real class that implements the protocol
- **Always test**: Make sure your mocks work with `with` statements before using them in tests

