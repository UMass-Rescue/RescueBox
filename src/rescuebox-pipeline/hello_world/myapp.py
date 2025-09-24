"""
This module defines a Celery application for orchestrating and executing distributed tasks.
It includes the Celery app instance, task definitions, and signal handlers for logging.

https://docs.celeryq.dev/en/main/getting-started/introduction.html

The Celery application is configured to use a local SQLite database for both the message broker
and the result backend. This setup is suitable for development and testing purposes.

The module includes several tasks:
- `add(x, y)`: A simple task that returns the sum of two numbers.
- `mul(x, y)`: A task that returns the product of two numbers.
- `sum_results(numbers)`: A callback task designed to sum a list of numbers, typically used with chords.
- `get_hello(name)`: A shared task that simulates a long-running job and returns a greeting.

A `task_prerun` signal handler is also defined to log the initiation of each task, providing visibility
into the task execution process.
"""

import logging
from time import sleep

from celery import Celery, shared_task
from celery.signals import task_prerun

# ==================================================================================================
# Logger Configuration
# ==================================================================================================
# Configure a logger for capturing task-related information.
# --------------------------------------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ==================================================================================================
# Celery Application Setup
# ==================================================================================================
# The Celery application is configured here, specifying the broker and result backend.
# For this example, we use a local SQLite database for both, which is convenient for development
# but not recommended for production environments.
# --------------------------------------------------------------------------------------------------

app = Celery(
    "myapp",
    result_backend="db+sqlite:///broker.db",
    broker="sqla+sqlite:///celerydb.db",
)

# Optional configuration to set the expiration time for task results.
app.conf.update(
    result_expires=3600,  # Results will be stored for 1 hour.
)


# ==================================================================================================
# Task Definitions
# ==================================================================================================
# These are the tasks that can be executed by the Celery workers. Each function is decorated
# with `@app.task` or `@shared_task` to register it as a Celery task.
# --------------------------------------------------------------------------------------------------


@app.task
def add(x, y):
    """A simple task that returns the sum of two numbers."""
    return x + y


@app.task
def mul(x, y):
    """A task that returns the product of two numbers."""
    return x * y


@app.task
def sum_results(numbers):
    """A callback task to sum the results from a group of tasks."""
    return sum(numbers)


@shared_task
def get_hello(name):
    """A shared task that simulates a long-running job and returns a greeting."""
    sleep(5)  # Simulate a 5-second delay.
    retval = f"Hello {name}"
    return retval


# ==================================================================================================
# Signal Handlers
# ==================================================================================================
# Signal handlers allow you to execute code in response to specific Celery events. In this case,
# we use the `task_prerun` signal to log when a task is about to be executed.
# --------------------------------------------------------------------------------------------------


@task_prerun.connect()
def log_celery_task_call(task, *args, **kwargs):
    """Log the initiation of a Celery task before it is executed."""
    print(f"Executing task: {task.name}")
    logger.info(f"Task '{task.name}' starting with args: {args}, kwargs: {kwargs}")


# ==================================================================================================
# Main Execution Block
# ==================================================================================================
# This block allows the Celery worker to be started directly by running this script.
# This is useful for development and testing.
# --------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    # Start the Celery worker when the script is executed directly.
    app.start()