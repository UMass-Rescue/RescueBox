# Celery "Hello World" Demo

This directory contains a simple demonstration of the Celery distributed task queue, showcasing its basic functionalities and concepts. The demo is designed to be run locally and provides a hands-on introduction to Celery's capabilities.

## Demo Overview

The demo consists of the following components:

- **`myapp.py`**: Defines the Celery application, including the broker and backend configurations, along with a set of tasks that can be executed.
- **`simple.py`**: A script that demonstrates various Celery patterns, such as chains, chords, and simple asynchronous tasks.
- **`task.py`**: An additional script for running tasks (optional).

## Prerequisites

Before running the demo, ensure you have the following installed:

- Python 3.x
- Celery ( from poertry pyproject.toml)
- SQLAlchemy ( from poertry pyproject.toml)



## Running the Demo

To run the demo, follow these steps:

1.  **Start the Celery Worker**:

    Open a terminal window, navigate to this directory, and run the following command to start the Celery worker:

    ```bash
    cd <RB_HOME>>\src\rescuebox-pipeline\rescuebox_pipeline\hello_world
    celery -A myapp worker -l DEBUG --pool=solo
    ```

2.  **Execute the Demo Script**:

    Open a second terminal window and run the `simple.py` script to see the Celery patterns in action:

    ```bash
    cd <RB_HOME>>\src\rescuebox-pipeline\rescuebox_pipeline\hello_world
    python simple.py
    ```

3.  **Optional Task Execution**:

    You can also run the `task.py` script for additional task examples:

    ```bash
    cd <RB_HOME>>\src\rescuebox-pipeline\rescuebox_pipeline\hello_world
    python task.py
    ```

## Additional Resources

For more information on Celery and its features, refer to the following resources:

- **Introduction to FastAPI and Celery**: https://derlin.github.io/introduction-to-fastapi-and-celery/03-celery/
- **Official Celery Documentation**: https://docs.celeryq.dev/en/main/getting-started/introduction.html
