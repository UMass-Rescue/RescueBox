# RescueBox Pipeline Demonstrations

This directory contains examples and demonstrations of how to build and orchestrate multi-step pipelines using Celery, with a focus on integrating with the RescueBox SDK for AI/ML workflows.

## Subdirectories

This directory is organized into two main subdirectories:

-   **`hello_world`**: A simple, self-contained demonstration of basic Celery concepts.
-   **`rescuebox-pipeline`**: A more advanced example showcasing how to build AI/ML pipelines using the RescueBox SDK and Celery.
     Note : rescuebox-pipeline needs rescuebox backend running , and python client code ( already generated here rescue_box_api_client)
---

## `hello_world` Demo

This demo provides a basic introduction to the Celery distributed task queue. It showcases fundamental patterns such as chains, chords, and simple asynchronous tasks.

### Running the Demo

1.  **Start the Celery Worker**:

    ```bash
    cd c:\work\rel\RescueBox\src\rescuebox-pipeline\hello_world
    celery -A myapp worker -l DEBUG --pool=solo
    ```

2.  **Execute the Demo Script**:

    ```bash
    cd c:\work\rel\RescueBox\rescuebox-pipeline\hello_world
    python simple.py
    ```

---

## `rescuebox_pipeline`

This example demonstrates how to build and run multi-step AI/ML pipelines using the RescueBox SDK, with Celery for task orchestration. It includes examples of chaining together different RescueBox plugins to create a complete workflow.

### Key Pipeline Examples
-   **`rp_pipeline3.py`**: A 2-step pipeline that demonstrates a `transcribe -> summarize` workflow. After 10 sec timeout kicks in and task in chain is aborted. another scenario can also be user cancelled the chain.
   
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
    cd c:\work\rel\RescueBox\rescuebox-pipeline\
    poetry run celery -A rescuebox_pipeline.rb_celery  worker -l DEBUG --pool=solo
    ```

3.  **Run a Pipeline Script**:

    ```bash
    cd c:\work\rel\RescueBox\rescuebox-pipeline\
    python rescuebox_pipeline/rb_pipeline.py
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

Developer tip : use the pre build docker container that has all these pre-reqs to quickly get going.
       edit the devcontainer.json and set image=nb887/rb-dev:2.1.1
       git checkout the hackathon branch with the rescuebox celery code-base

## Additional Resources

-   **Official Celery Documentation**: [https://docs.celeryq.dev/en/main/getting-started/introduction.html](https://docs.celeryq.dev/en/main/getting-started/introduction.html)
