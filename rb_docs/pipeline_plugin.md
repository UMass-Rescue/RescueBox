# Pipeline Architecture Design

## 1. Introduction

This document outlines a hybrid architecture for creating, executing, and discovering complex, multi-step pipelines in RescueBox. The design combines configuration-driven code generation for robust backend execution with a dynamic "proxy" plugin to ensure seamless frontend integration.

## 2. Architecture Overview

The architecture is composed of several key components that work together:

1.  **`pipelines.yaml` (The Recipe)**: The single source of truth where users define pipelines as a sequence of services.

2.  **Plugin-Provided Celery Tasks (`rb_celery.py`)**: A manually-maintained Python file where plugin developers create Celery `@shared_task`s that wrap calls to their plugin's API service.

3.  **`PipelineGenerator` (Backend Code Generator)**: A script that reads `pipelines.yaml` and generates `rb_pipeline.py`, which contains the Celery `chain` definitions for the backend execution of pipelines.

4.  **`pipelines-plugin` (Frontend Proxy)**: A new, static RescueBox plugin that makes pipelines discoverable by the frontend. It reads `pipelines.yaml` and exposes a RESTful API for each pipeline, providing the necessary `task_schema` for UI rendering.

5.  **`ML_REGISTRY` (Schema Discovery)**: A registry populated by all plugins at startup. The `pipelines-plugin` uses this to fetch the `task_schema` for a pipeline's initial task, which it then serves as the schema for the entire pipeline.

## 3. Component Deep Dive

### 3.1. `pipelines.yaml`

This file defines the service-to-task mapping and the pipeline sequences.

```yaml
# Maps a service identifier to a manually-created Celery task
services:
  audio/transcribe:
    celery_task: run_audio_plugin
  text_summarization/summarize:
    celery_task: run_text_summarization_plugin

# Defines pipelines as a sequence of services
pipelines:
  - name: audio_to_summary
    short_title: "Audio to Summary"
    tasks:
      - service: audio/transcribe
      - service: text_summarization/summarize
        parameters:
          model: gemma3:1b
```

### 3.1.1. Example: 3-Step Pipeline

The design supports pipelines of any length, including multiple services from the same plugin. Here is how a more complex 3-step pipeline would be defined:

```yaml
services:
  facematch/enroll_face:
    celery_task: run_facematch_enroll_task
  facematch/find_matches:
    celery_task: run_facematch_find_task
  deepfake/detect:
    celery_task: run_deepfake_detect_task

pipelines:
  - name: enroll_match_and_detect
    short_title: "Face Match and Deepfake Detection Pipeline"
    tasks:
      - service: facematch/enroll_face
      - service: facematch/find_matches
      - service: deepfake/detect
```

### 3.2. `rb_celery.py` (Manual)

Plugin developers add tasks here to make their services available to the pipeline system.

```python
# pipeline/rescuebox_pipeline/rb_celery.py

from celery import shared_task
from rescue_box_api_client import Client
from rescue_box_api_client.api.audio import rb_audio_transcribe_post
from rescue_box_api_client.models import BodyAudioTranscribePost, DirectoryInput

# This should be configured properly
API_CLIENT = Client(base_url="http://localhost:8000")

@shared_task
def run_audio_plugin(input_path: str):
    """Celery task to run the audio transcription plugin via API."""
    body = BodyAudioTranscribePost(inputs={"input_dir": DirectoryInput(path=input_path)})
    response = rb_audio_transcribe_post.sync(client=API_CLIENT, body=body)
    # The return value of this task is passed to the next task in the chain
    return response.root.texts[0].value

# ... other manually-written tasks ...
```

**Note on Data Transformation**: If the output of one task is not in the exact format required by the next, a developer can create a small, intermediate Celery task (e.g., `save_text_to_file.s(...)`) and insert it into the pipeline chain in `pipelines.yaml` to handle the data conversion.

### 3.3. `PipelineGenerator` (`rescuebox/pipeline_loader.py`)

This script generates `rb_pipeline.py`.

```python
# rescuebox/pipeline_loader.py
# (Content as previously defined - generates chains in rb_pipeline.py)
# ...
```

### 3.4. `pipelines-plugin` (New Plugin)

This new plugin makes pipelines visible to the frontend.

**`src/pipelines-plugin/pipelines_plugin/main.py`:**

```python
import yaml
import typer
from rb.lib.ml_service import MLService, get_ml_schema_func
from rb.api.models import ResponseBody, TextResponse
# Import the Celery chain trigger functions from the generated rb_pipeline.py
# This will be a dynamic import based on the generated file
from pipeline.rescuebox_pipeline import rb_pipeline

APP_NAME = "pipelines"
ml_service = MLService(APP_NAME)

# Load pipeline definitions
with open('pipelines.yaml', 'r') as f:
    config = yaml.safe_load(f)

for pipeline_def in config.get('pipelines', []):
    pipeline_name = pipeline_def['name']
    short_title = pipeline_def['short_title']
    first_task = pipeline_def['tasks'][0]['service']

    # Get the schema from the first task using the registry
    schema_func = get_ml_schema_func(first_task)

    if not schema_func:
        print(f"Warning: Could not find schema for service '{first_task}'. Pipeline '{pipeline_name}' will not be available in the UI.")
        continue

    # This is the function that will be called by the API
    def create_pipeline_trigger(p_name):
        def trigger_pipeline(inputs) -> ResponseBody:
            # This function's job is to trigger the Celery pipeline.
            pipeline_runner = getattr(rb_pipeline, f"run_{p_name}_pipeline")
            initial_arg = inputs['input_dir'].path # This needs to be generic
            pipeline_runner.delay(initial_arg) # .delay() runs the Celery task asynchronously
            return ResponseBody(root=TextResponse(value=f"Pipeline '{p_name}' started."))
        return trigger_pipeline

    # Create a CLI parser for the pipeline's input
    # This also needs to be generated dynamically based on the schema
    def create_cli_parser():
        def cli_parser(path: str):
            from rb.api.models import DirectoryInput
            return {"input_dir": DirectoryInput(path=path)}
        return cli_parser

    ml_service.add_ml_service(
        rule=f"/{pipeline_name}",
        ml_function=create_pipeline_trigger(pipeline_name),
        inputs_cli_parser=typer.Argument(parser=create_cli_parser(), help="Initial input for the pipeline"),
        task_schema_func=schema_func, # Use the schema from the first task!
        short_title=short_title,
    )

app = ml_service.app
```

## 4. Summary of Flow

1.  **Build Time**: A developer runs `PipelineGenerator` to create or update `rb_pipeline.py` based on `pipelines.yaml`.

2.  **App Startup**: All plugins are loaded, including the new `pipelines-plugin`. The `ML_REGISTRY` is populated with schema information from all started services.

3.  **Frontend Discovery**: The UI discovers a single plugin named "pipelines". It calls the `/pipelines/api/routes` endpoint and receives a list of all available pipelines (e.g., `audio_to_summary`, `video_to_gif`) as distinct, runnable tasks within that single plugin.

4.  **UI Rendering**: To render the inputs for a specific pipeline (e.g., `audio_to_summary`), the UI calls that task's schema endpoint (`/pipelines/audio_to_summary/task_schema`). The `pipelines-plugin` intercepts this and serves the schema of the *first* service in that pipeline's chain (retrieved from the `ML_REGISTRY`).

5.  **Execution**: The user provides the initial inputs in the UI and clicks "Run". The UI makes a single API call to the selected pipeline's endpoint (e.g., `/pipelines/audio_to_summary`).

6.  **Backend Trigger**: The `pipelines-plugin` receives this API call and its `ml_function` triggers the corresponding Celery chain asynchronously, passing the initial inputs.

7.  **Backend Processing**: Celery workers pick up the pipeline task and execute the chain of services in the background.
