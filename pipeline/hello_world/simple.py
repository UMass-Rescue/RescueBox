"""
This script demonstrates the use of Celery for orchestrating and executing tasks in a distributed manner.
It showcases three fundamental Celery patterns: chains, chords, and simple task execution.

- **Chains**: A sequence of tasks where the output of one task becomes the input for the next.
- **Chords**: A set of tasks that run in parallel, with a callback task that executes after all parallel tasks are complete.
- **Simple Task**: A single, independent task that is executed asynchronously.

The script interacts with a Celery application defined in the `myapp` module, which includes tasks for addition,
multiplication, and summing results. The results of these tasks are retrieved and printed to the console to
illustrate the execution flow and the outcome of each pattern.
"""

from celery import chain, chord, group
from celery.result import AsyncResult
from myapp import add, get_hello, mul, sum_results
from myapp import app

# ==================================================================================================
# Chain Example: (1 + 1) + 4 = 6
# ==================================================================================================
# A chain is a sequence of tasks where the output of one task is passed as input to the next.
# In this example, we first add 1 + 1, and then add 4 to the result.
# --------------------------------------------------------------------------------------------------

print("=" * 80)
print("Chain Example: (1 + 1) + 4")
print("-" * 80)

# Create a chain of two 'add' tasks. The first adds 1+1, the second adds 4 to the result.
res = chain(add.s(1, 1), add.s(4))()

print(f"Step 1 (1 + 1) result: {res.parent.get()}")
print(f"Chain pipeline result (2 + 4): {res.get()}")
print("=" * 80)


# ==================================================================================================
# Chord Example: (1 + 1) + (2 * 2) = 6
# ==================================================================================================
# A chord consists of a group of tasks that run in parallel, followed by a callback task that
# executes after all parallel tasks have completed. In this example, we run two tasks in parallel:
# one for addition (1 + 1) and one for multiplication (2 * 2). The results of these tasks are
# then passed to a 'sum_results' task.
# --------------------------------------------------------------------------------------------------

print("\n" * 2)
print("=" * 80)
print("Chord Example: (1 + 1) + (2 * 2)")
print("-" * 80)

# Create a group of parallel tasks: add(1, 1) and mul(2, 2).
parallel_tasks = group(add.s(1, 1), mul.s(2, 2))

# Create a chord where 'sum_results' is the callback that receives the results of the parallel tasks.
res = chord(parallel_tasks)(sum_results.s())

print(f"Chord pipeline result (sum of (1+1, 2x2)): {res.get()}")
print("=" * 80)


# ==================================================================================================
# Simple Asynchronous Task Example
# ==================================================================================================
# This example demonstrates the execution of a single, long-running task asynchronously.
# The 'get_hello' task is called with a delay, which means it runs in the background without
# blocking the main application. We then retrieve the result using the task's ID.
# --------------------------------------------------------------------------------------------------

print("\n" * 2)
print("=" * 80)
print("Simple Asynchronous Task Example")
print("-" * 80)

print("Starting long-running job: get_hello('foo')")
result = get_hello.delay("foo")
print(f"Job ID: {result.id}")

# Retrieve the result using the task ID.
res = AsyncResult(result.id, app=app)

print(f"Job status: {res.state}")
# The .get() method is a blocking call that waits for the task to complete.
print(f"Job output: {res.get()}")
print("=" * 80)