# RescueBox Pipeline Demonstrations

This directory contains examples and demonstrations of how to build and orchestrate multi-step pipelines using Celery, with a focus on integrating with the RescueBox SDK for AI/ML workflows.

## Subdirectories

This directory is organized into two main subdirectories:

-   **`hello_world`**: A simple, self-contained demonstration of basic Celery concepts.
-   **`rescuebox_pipeline`**: A more advanced example showcasing how to build AI/ML pipelines using the RescueBox SDK and Celery.
     Note : rescuebox_pipeline needs rescuebox backend running , and python client code ( already generated here rescue_box_api_client)
---

## `hello_world` Demo

This demo provides a basic introduction to the Celery distributed task queue. It showcases fundamental patterns such as chains, chords, and simple asynchronous tasks.

### Running the Demo

1.  **Start the Celery Worker**:

    ```bash
    cd c:\work\rel\RescueBox\pipeline\hello_world
    celery -A myapp worker -l DEBUG --pool=solo
    ```

2.  **Execute the Demo Script**:

    ```bash
    cd c:\work\rel\RescueBox\pipeline\hello_world
    python simple.py
    ```

---

## `rescuebox_pipeline`

This example demonstrates how to build and run multi-step AI/ML pipelines using the RescueBox SDK, with Celery for task orchestration. It includes examples of chaining together different RescueBox plugins to create a complete workflow.

### Key Pipeline Examples

-   **`rp_pipeline2.py`**: A 3-step pipeline that demonstrates a `transcribe -> save_text_to_file -> summarize` workflow.
-   **`rb_pipeline.py`**: A `transcribe -> summarize` pipeline that also shows how to start and then cancel a running pipeline.

### Running the Pipeline

1.  **Start the RescueBox Backend**:

    ```bash
    cd c:\work\rel\RescueBox
    poetry run python -m src.rb-api.rb.api.main
    ```

2.  **Start the Celery Worker**:

    ```bash
    cd c:\work\rel\RescueBox\pipeline\rescuebox_pipeline
    celery -A rb_celery worker -l DEBUG --pool=solo
    ```

3.  **Run a Pipeline Script**:

    ```bash
    cd c:\work\rel\RescueBox\pipeline\rescuebox_pipeline
    python rp_pipeline2.py
    ```

---

## Prerequisites

-   Python 3.x
-   Celery
-   RabbitMQ
-   Docker
-   Poetry
-   FFmpeg
-   Ollama
-   SQLAlchemy
-   RescueBox backend running
-   For the `rescuebox_pipeline`:
    -   `ffmpeg` installed
    -   `ollama` server running with the `llama3.2:3b` model

## Additional Resources

-   **Official Celery Documentation**: [https://docs.celeryq.dev/en/main/getting-started/introduction.html](https://docs.celeryq.dev/en/main/getting-started/introduction.html)
