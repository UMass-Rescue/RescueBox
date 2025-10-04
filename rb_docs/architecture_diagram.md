# RescueBox Architecture Diagram

This document provides a visual representation of the RescueBox system architecture, focusing on how the pipeline orchestration layer interacts with the backend API and its plugins.

## Diagram

```
+---------------------------+      +---------------------------+      +--------------------------------+
|   Pipeline Client         |      |   YAML-Driven UI          |      |    Developer Tools             |
| (e.g., rp_pipeline2.py)   |      |   (pipelines-plugin)      |      |  (e.g., openapi-python-client) |
+-------------+-------------+      +-------------+-------------+      +----------------+---------------+
              |                            |                                           |
  (1. Creates Celery Chain)                | (A. Reads pipelines.yaml)                 | (Generates)
              |                            |                                           |
              |                            | (B. Triggers Watcher Task)                v
              |                            |                      +--------------------+---------------------+
              |                            +--------------------->|  rescue-box-api-client (Generated SDK)   |
              |                                                   +--------------------+---------------------+
              |                                                                        ^
              |                                                                        | (Used by)
              v                                                                        |
+-------------+------------------------------------------------------------------------+-------------+
|                                  Pipeline Orchestration Layer (rescuebox-pipeline)                 |
|                                                                                                    |
|   +-------------------------+        +-------------------------+        +------------------------+   |
|   |  rb_celery.py           |        |  RabbitMQ (Broker)      |        |  Filesystem            |   |
|   | (Defines Celery App &   |        | (Message Queue)         |        | (Result Backend)       |   |
|   |  Wrapper Tasks)         |        +-------------------------+        +------------------------+   |
|   +-------------------------+                 ^      |                         ^      |              |
|              | (2. Sends Task)                |      | (4. Fetches Task)       |      | (7. Stores   |
|              +------------------------------->+      |                         |      |   Result)    |
|                                                      v                         |      v              |
|                                          +-----------+-----------+             |  +---+--------------+ |
|                                          |   Celery Worker       |-------------+  | AsyncResult    | |
|                                          | (Executes Tasks)      | (6. Reports     | (Task State &  | |
|                                          +-----------------------+   Status)       |  Return Value) | |
|                                                     |                              +----------------+ |
|                                (5. Executes Wrapper Task)                                            |
|                                                     |                                                |
|                                                     v (Makes API Call via SDK)                       |
+-----------------------------------------------------+------------------------------------------------+
                                                      |
                                                      | (3. HTTP Request)
                                                      v
+-----------------------------------------------------+------------------------------------------------+
|                                     RescueBox Backend (rb-api)                                       |
|                                                                                                    |
|   +-------------------------+      +----------------------------+      +-------------------------+   |
|   |  FastAPI App (main.py)  |----->|  Dynamic Router (cli.py)   |----->|  Plugin Endpoints       |   |
|   | (Serves openapi.json)   |      | (Generates API from Typer) |      | (e.g., /audio/transcribe)|   |
|   +-------------------------+      +----------------------------+      +-----------+-------------+   |
|                                                                                    |                 |
|                                                                                    | (Invokes)       |
|                                                                                    v                 |
|                                                                      +-------------+-----------+     |
|                                                                      |   Individual Plugins    |     |
|                                                                      | (e.g., audio-transcription) | |
|                                                                      +-------------------------+     |
|                                                                                    |                 |
+------------------------------------------------------------------------------------+-----------------+
                                                                                     |
                                                                                     | (Uses External Tools)
                                                                                     v
                                                                    +----------------+-----------------+
                                                                    |  External Services & Libraries   |
                                                                    | (Ollama, FFmpeg, etc.)           |
                                                                    +----------------------------------+

```

## Explanation of the Flow (Script-Based)

1.  **Client Creates Chain**: A script like `rp_pipeline2.py` defines a sequence of tasks using Celery's `chain` and sends the first task to the broker.
2.  **Task Queued**: The task is placed on the **RabbitMQ** message queue.
3.  **API Call**: The **Celery Worker** picks up the task. The task's logic (in `rb_celery.py`) uses the **`rescue-box-api-client`** to make an HTTP request to the **RescueBox Backend**.
4.  **Backend Processing**: The backend's **FastAPI** app routes the request to the appropriate plugin (e.g., `audio-transcription`), which performs its work, potentially using external tools like **Ollama**.
5.  **Response and Result**: The plugin returns its result. The Celery task receives the HTTP response, processes it, and stores its final state and return value in the **Filesystem Result Backend**.
6.  **Next Task**: The worker then places the next task in the chain onto the RabbitMQ queue, passing the result of the previous task as input. This continues until the pipeline is complete.