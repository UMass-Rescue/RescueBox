# Understanding `run_in_executor` in `call_granite_model_direct` Tests

## The Problem

The `call_granite_model_direct` method uses `asyncio.run_in_executor()` to run synchronous operations (model loading and inference) in a thread pool without blocking the event loop. When testing this method, we need to properly mock `run_in_executor` to behave correctly.

## How `run_in_executor` Works

```python
# In core.py (lines 562, 579)
self._llama_model = await loop.run_in_executor(None, load_model)
model_output = await loop.run_in_executor(None, run_inference)
```

### Key Points:

1. **`run_in_executor` is NOT a regular function** - It's an async method that:
   - Takes a function to run in a thread pool
   - Returns a **coroutine/awaitable** (not the direct result)
   - Must be `await`ed to get the actual result

2. **Why it returns a coroutine**:
   - The function execution happens asynchronously in a thread pool
   - The coroutine resolves when the thread completes
   - This allows other async operations to continue while waiting

## The Test Issue

When mocking `run_in_executor` in tests, we need to ensure:

1. **It returns an awaitable** - The mock must return something that can be `await`ed
2. **It executes the function** - The function passed to it should actually run (for testing)
3. **It returns the function's result** - After awaiting, we should get the function's return value

## The Solution

```python
# Correct approach (current implementation)
import asyncio
mock_loop = MagicMock()

async def mock_run_in_executor(executor, func, *args):
    # Execute function immediately and return result
    if args:
        return func(*args)
    return func()

mock_loop.run_in_executor = mock_run_in_executor

with patch('asyncio.get_event_loop', return_value=mock_loop):
    result = await core.call_granite_model_direct("transcribe audio", str(model_file))
```

### Why This Works:

1. **`async def`** makes the mock function return a coroutine
2. **The function executes immediately** - Good for unit tests (no threading needed)
3. **Returns the actual result** - When awaited, returns what the function returned
4. **Can be awaited** - `await loop.run_in_executor(...)` works correctly

## What Would NOT Work

```python
# ❌ WRONG - Returns result directly, not awaitable
def mock_run_in_executor(executor, func):
    return func()  # This is NOT a coroutine!

mock_loop.run_in_executor = mock_run_in_executor
# This would fail: await loop.run_in_executor(...) 
# TypeError: object function is not awaitable
```

```python
# ❌ WRONG - Lambda can't be async easily
mock_loop.run_in_executor = lambda executor, func: func()
# Same issue - not awaitable
```

## Real-World Flow

In production:
```python
# 1. Call run_in_executor (returns coroutine immediately)
coro = loop.run_in_executor(None, load_model)

# 2. Await coroutine (blocks until thread completes)
model = await coro  # model = Llama(...)
```

In tests:
```python
# 1. Call mock_run_in_executor (returns coroutine immediately)
coro = mock_run_in_executor(None, load_model)

# 2. Await coroutine (executes function immediately, returns result)
model = await coro  # model = Mock(...) - executes load_model() immediately
```

## Summary

- `run_in_executor` must return a coroutine (awaitable)
- The mock function must be `async def` to return a coroutine
- The function executes immediately in tests (no real threading needed)
- This allows `await loop.run_in_executor(...)` to work correctly

