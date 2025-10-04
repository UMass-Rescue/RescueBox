# RescueBox Pipeline Architecture

## 1. Introduction

This document outlines the architecture for creating, executing, and monitoring complex, multi-step pipelines in RescueBox. The design uses Celery as the core orchestration engine to chain together tasks, where each task typically wraps an API call to a standalone RescueBox plugin service.

This architecture supports two primary methods for defining and running pipelines:

1.  **Script-Based Pipelines (Recommended)**: A direct and flexible method where pipelines are defined as Celery `chain` objects within standard Python scripts. This is the most robust and currently demonstrated approach.
2.  **YAML-Driven Pipelines**: A declarative approach where pipelines are defined in a `pipelines.yaml` file and exposed to the frontend via a dedicated `pipelines-plugin`. This offers better UI integration but is more complex.

## 2. Core Concepts

### 2.1. Celery Tasks (`rb_celery.py`)

The fundamental building blocks of any pipeline are Celery tasks. These are Python functions decorated with `@shared_task` that reside in `c:\work\rel\RescueBox\src\rescuebox-pipeline\rescuebox_pipeline\rb_celery.py`. For a detailed explanation of the Celery setup, including the broker and result backend, please refer to the Celery Setup and Configuration Guide.

Each task serves as a wrapper that makes an API call to a specific RescueBox plugin service (e.g., audio transcription, text summarization). They handle the communication and data marshalling between the pipeline and the plugin's backend.

**Example: An Audio Transcription Task**
```python
# c:\work\rel\RescueBox\src\rescuebox-pipeline\rescuebox_pipeline\rb_celery.py

from rescue_box_api_client import Client
from rescue_box_api_client.api.audio import rb_audio_transcribe_post

client = Client(base_url="http://localhost:8000", verify_ssl=False)

@shared_task(bind=True, base=AbortableTask, name="rescuebox_pipeline.rb_celery.run_audio_plugin")
def run_audio_plugin(self, path: Path) -> Path:
    # ... logic to construct the request body ...

    # Uses the auto-generated API client to call the backend service
    transcribe_out = rb_audio_transcribe_post.sync(
        client=client,
        streaming=False,
        body=request_body,
    )

    # ... logic to process the response, save to a file ...
    
    # Returns the path to the output file, which is passed to the next task in a chain
    return text_out_path.resolve()
```

### 2.2. Pipeline Scripts

These are Python scripts (e.g., `rp_pipeline2.py`, `rb_pipeline3_fixed.py`) that act as the entry point for defining and executing a pipeline. They import the necessary tasks from `rb_celery.py` and arrange them into a Celery `chain` to define the sequence of operations. These tasks rely on a generated API client to communicate with the backend. For more information, see the API Client Generation Guide.


## 3. Approach 1: Script-Based Pipelines (Recommended)

This is the recommended approach for its simplicity and power. The developer has full control over the pipeline's logic and execution flow directly in Python.

### 3.1. Defining a Simple Chain (`rp_pipeline2.py`)

This example demonstrates a 3-step pipeline: transcribe audio, save the resulting text to a file, and then summarize that text.

```python
# c:\work\rel\RescueBox\src\rescuebox-pipeline\rescuebox_pipeline\rp_pipeline2.py

from celery import chain
from rb_celery import (
    run_audio_plugin_get_text,
    save_text_to_file,
    run_text_summarization_plugin,
)

# ... define input and output paths ...

# Define the pipeline as a chain of task signatures.
# The output of each task is automatically passed as the first argument to the next.
result = chain(
    run_audio_plugin_get_text.s(path=audio_mp3_path),
    save_text_to_file.s(intermediate_text_path),
    run_text_summarization_plugin.s(
        inputs={"output_dir": str(output_summarize_path)},
        parameters={"model_name": "llama3.2:3b"},
    ),
)() # The final () executes the chain.
```

### 3.2. Client-Side Monitoring & Cancellation (`rb_pipeline3_fixed.py`)

For long-running pipelines, it is critical to handle monitoring, timeouts, and cancellation from the client script, not from within another Celery task. This avoids deadlocks where a "watcher" task occupies a worker that is needed to run the pipeline it's watching.

```python
# c:\work\rel\RescueBox\src\rescuebox-pipeline\rescuebox_pipeline\rb_pipeline3_fixed.py

from celery.exceptions import TimeoutError

# ... create pipeline_chain ...

# Execute the pipeline asynchronously
pipeline_result = pipeline_chain.apply_async()

print(f"Pipeline started with ID: {pipeline_result.id}...")

try:
    # Block and wait for the final result, with a timeout.
    final_outcome = pipeline_result.get(timeout=20)
    print("--- Pipeline Finished Successfully ---")

except TimeoutError:
    print("--- Pipeline Timed Out ---")
    # Logic to find and revoke all tasks in the chain.
    task_to_revoke = AbortableAsyncResult(pipeline_result.id, app=app)
    while task_to_revoke:
        print(f"Revoking task: {task_to_revoke.id}")
        task_to_revoke.abort()
        app.control.revoke(task_to_revoke.id, terminate=True)
        task_to_revoke = task_to_revoke.parent
```


## 4. How to Run the Examples

Please refer to the `c:\work\rel\RescueBox\src\rescuebox-pipeline\README.md` file for a complete list of prerequisites, including RabbitMQ, Ollama, and FFmpeg.

### 4.1. Running the `hello_world` Demo

This simple demo introduces basic Celery concepts and does not require the full RescueBox backend.

1.  **Start the Celery Worker**:
    ```bash
    cd c:\work\rel\RescueBox\src\rescuebox-pipeline\hello_world
    celery -A myapp worker -l DEBUG --pool=solo
    ```

2.  **Execute the Demo Script**:
    In a separate terminal:
    ```bash
    cd c:\work\rel\RescueBox\src\rescuebox-pipeline\hello_world
    python simple.py
    ```

### 4.2. Running the RescueBox Pipelines demo

These examples require the full RescueBox backend and a Celery worker to be running.

1.  **Start the RescueBox Backend**:
    In a terminal at the project root:
    ```bash
    cd c:\work\rel\RescueBox
    poetry run python -m src.rb-api.rb.api.main
    ```

2.  **Start the Celery Worker**:
    In a separate terminal:
    ```bash
    cd c:\work\rel\RescueBox\src\rescuebox-pipeline\rescuebox_pipeline
    poetry run celery -A rescuebox_pipeline.rb_celery worker -l DEBUG --pool=solo
    ```

3.  **Run a Pipeline Script**:
    Once the backend and worker are running, execute one of the pipeline scripts in a third terminal.

    *   **For the 3-step pipeline:**
        ```bash
        cd c:\work\rel\RescueBox\src\rescuebox-pipeline\rescuebox_pipeline
        python rescuebox_pipeline\rp_pipeline2.py
        ```

    *   **For the timeout/cancellation demo:**
        ```bash
        cd c:\work\rel\RescueBox\src\rescuebox-pipeline\rescuebox_pipeline
        python rescuebox_pipeline\rb_pipeline3_fixed.py
        ```
