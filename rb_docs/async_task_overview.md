# Asynchronous Task Execution in RescueBox

This document provides an overview of the asynchronous task execution feature in RescueBox, designed to handle long-running processes without blocking the user interface.

## 1. Feature Overview

The asynchronous workflow is designed for operations that may take a significant amount of time, such as machine learning model inference. Instead of making the user wait for the entire process to complete, the system immediately acknowledges the request, starts the task in the background, and provides a way for the client to check on the progress and retrieve the result when it's ready.

This is achieved through a two-step process:
1.  **Task Initiation**: The client sends an initial request to start the task. The server queues the job and immediately responds with a unique **Task ID**.
2.  **Result Polling**: The client uses the Task ID to periodically query a separate endpoint to check the task's status. Once the task is complete, this endpoint returns the final result.

---

## 2. The Asynchronous Flow

The interaction between the client (the `rescuebox-autoui` web interface) and the backend follows these steps:

1.  **POST Request**: The client sends a `POST` request to an async-enabled endpoint (e.g., `/audio/transcribe`).
2.  **Task ID Response**: The server receives the request, initiates a background job via Celery, and immediately returns a `202 Accepted` response containing the Task ID.
    ```json
    {
      "root": {
        "title": "task_id",
        "value": "ab8b533a-7a33-451a-901b-b56349058792"
      }
    }
    ```
3.  **Polling with GET**: The client constructs a new polling URL from the original endpoint and the Task ID (e.g., `/audio/transcribe/result/ab8b533a-7a33-451a-901b-b56349058792`) and begins sending `GET` requests to it.
4.  **Status Updates**: As long as the task is running, the server responds with the current status.
    ```json
    {
      "root": {
        "title": "status",
        "value": "Task status: PENDING"
      }
    }
    ```
5.  **Final Result**: Once the background job is finished, the polling endpoint responds with the final, complete result of the operation.

---

## 3. Backend Implementation

The backend relies on a combination of Celery for background task management and the `MLService` helper for dynamically creating the necessary API endpoints.

### 3.1. Creating a Celery Task (Example: Audio Transcription)

Any function intended to be run asynchronously must be decorated with `@shared_task` from our central Celery application instance. This registers it with the Celery worker.

**File**: `src/audio-transcription/audio_transcription/main.py`
```python
from rescuebox_pipeline.rb_celery import shared_task

# The `@shared_task` decorator turns this function into a background job.
# `bind=True` allows access to task metadata like the request ID.
@shared_task(bind=True)
def transcribe_task(self, inputs: AudioInput) -> ResponseBody:
    """
    This is the Celery task that performs the long-running transcription.
    It runs in the background, allowing the API to remain responsive.
    """
    logger.info(f"Task {self.request.id}: Starting async transcription.")
    
    # --- Main logic for the task ---
    dirpath = DirectoryPath(inputs["input_dir"].path)
    results = model.transcribe_files_in_directory(dirpath)
    
    # The task is responsible for formatting the final, successful response.
    result_texts = [
        TextResponse(value=r["result"], title=str(r["file_path"])) for r in results
    ]
    response = BatchTextResponse(texts=result_texts)
    
    logger.info(f"Task {self.request.id}: Async transcription finished.")
    return ResponseBody(root=response)
```

### 3.2. Registering the Service with `MLService`

The `MLService` helper abstracts away the complexity of creating the two-step API endpoints. By setting `is_async=True`, we instruct it to generate both the initial task creation endpoint and the subsequent result polling endpoint.

**File**: `src/rb-lib/rb/lib/ml_service.py`
```python
# In the audio plugin's main.py
ml_service.add_ml_service(
    rule="/transcribe",
    ml_function=transcribe_task, # Pass the Celery task function
    ...
    # This flag enables the entire async workflow for this endpoint.
    is_async=True
)
```

When `is_async=True`, `MLService` does the following:
1.  Creates the main `POST` endpoint (`/audio/transcribe`) that calls `.apply_async()` on the Celery task and returns the `task.id`.
2.  Dynamically creates a new `GET` endpoint (`/audio/transcribe/result/{task_id}`) that checks the Celery task's status (`AsyncResult`) and returns either the status or the final result.

### 3.3. API Routing

The API router in `src/rb-api/rb/api/routes/cli.py` is configured to correctly handle the polling endpoint. It identifies URLs containing `/result/` as `GET` requests, ensuring that clients can poll for results correctly.

---

## 4. Frontend Implementation (`rescuebox-autoui`)

The frontend React application in `web/rescuebox-autoui` contains the client-side logic for interacting with async endpoints.

**File**: `web/rescuebox-autoui/src/App.jsx`

### 4.1. Starting the Task

When the user runs a command, the `handleRunCommand` function sends the initial `POST` request. It then inspects the response to see if it contains a `task_id`.

```javascript
// In handleRunCommand...
const response = await fetch(url, { ... });
const parsedData = await response.json();

// Check for a task_id in the response to start polling
if (parsedData && parsedData.root.title === "task_id") {
    const taskId = parsedData.root.value;
    const resultUrl = `${selectedCommand.endpoint}/result/${taskId}`;
    
    setCommandOutput(`Task started with ID: ${taskId}. Polling for result...`);
    setIsPolling(true);
    pollForResult(resultUrl); // Start polling for the result
} else {
    // This is a synchronous command, display the result directly
    setCommandOutput(JSON.stringify(parsedData, null, 2));
}
```

### 4.2. Polling for the Result

The `pollForResult` function is responsible for repeatedly checking the result endpoint until the task is complete.

```javascript
const pollForResult = async (resultUrl) => {
    try {
        // Send a GET request to the polling endpoint
        const resultResponse = await fetch(resultUrl, { method: "GET" });
        const resultData = await resultResponse.json();

        // Check if the task is still pending
        if (resultData && resultData.root.title === "status" && resultData.root.value.includes("PENDING")) {
            // If pending, update the UI and poll again after a delay
            setCommandOutput((prev) => prev + " .");
            setTimeout(() => pollForResult(resultUrl), 5000); // 5-second delay
        } else {
            // Task is done, display the final result
            setCommandOutput(JSON.stringify(resultData, null, 2));
            setIsPolling(false); // Stop polling
        }
    } catch (error) {
        // Handle polling errors
        setCommandOutput((prev) => prev + `\n Polling Error: ${error.message}`);
        setIsPolling(false);
    }
};
```
