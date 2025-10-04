# Celery Setup and Configuration Guide

This document provides a detailed explanation of the Celery configuration used in the RescueBox pipeline architecture. A correctly configured Celery environment is essential for managing and executing distributed tasks.

## 1. Broker (Message Queue)

The broker is the central message transport system. It receives tasks from clients (your pipeline scripts) and holds them in a queue until a Celery worker is available to process them.

*   **Configuration**: The system is configured to use RabbitMQ as its broker. This is specified in `rb_celery.py`:
    ```python
    broker="pyamqp://guest@localhost//"
    ```
*   **Why RabbitMQ?**: It is a robust, feature-rich, and production-ready message broker that is highly recommended by the Celery project for complex workflows.
*   **Requirement**: A RabbitMQ server must be running and accessible on the local machine for the pipeline system to function.

## 2. Result Backend

The result backend is a storage system where Celery workers save the state (`PENDING`, `SUCCESS`, `FAILURE`) and return values of completed tasks. This is crucial for retrieving the final output of a pipeline and for monitoring its progress.

*   **Configuration**: The system uses the local filesystem as its result backend, as configured in `rb_celery.py`:
    ```python
    result_backend="file://c:/work/rel/RescueBox/results/"
    ```
*   **Why Filesystem?**: While Celery supports many backends (like databases or RPC), the filesystem backend has proven to be the most reliable for this project's Windows environment. It fully supports essential features like task cancellation (`abort`/`revoke`), which did not work as expected with other backends like `rpc://` on Windows.

## 3. Celery Worker

The Celery worker is the core process that executes the tasks. It continuously monitors the message queue for new jobs, runs them, and reports the status and results to the configured result backend.

*   **Starting the Worker**: The worker is started from the command line with a specific command:
    ```bash
    # Run from c:\work\rel\RescueBox\src\rescuebox-pipeline
    poetry run celery -A rescuebox_pipeline.rb_celery worker -l DEBUG --pool=solo
    ```
*   **Command Breakdown**:
    *   `-A rescuebox_pipeline.rb_celery`: Points to the Celery application instance (named `app`) located inside the `rb_celery.py` module within the `rescuebox_pipeline` package.
    *   `worker`: The command to start a worker process.
    *   `-l DEBUG`: Sets the logging level to `DEBUG` for maximum verbosity, which is very helpful for development and troubleshooting.
    *   `--pool=solo`: This is a critical setting for Windows development. It forces the worker to use a single-threaded execution pool, which prevents many concurrency-related issues and makes debugging much more straightforward.
