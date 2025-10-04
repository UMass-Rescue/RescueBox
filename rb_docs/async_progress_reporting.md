# Asynchronous Task Progress Reporting

This document outlines an enhancement to the asynchronous task execution feature in RescueBox to support real-time progress reporting for long-running jobs.

## 1. Feature Overview

While the existing async feature prevents the UI from blocking, users lack visibility into the progress of a task. This enhancement provides a standardized way for a background task to report its progress (e.g., as a percentage) back to the client, which can then be displayed to the user.

This is achieved by leveraging Celery's ability to store custom metadata with a task's state.

---

## 2. The Enhanced Asynchronous Flow

The flow is updated to include an intermediate progress state during polling:

1.  **POST Request**: The client sends a `POST` request to an async-enabled endpoint (e.g., `/audio/transcribe`).
2.  **Task ID Response**: The server initiates the background job and immediately returns a `202 Accepted` response with a **Task ID**.
3.  **Polling with GET**: The client begins polling the result endpoint (e.g., `/audio/transcribe/result/{task_id}`).
4.  **Progress Updates (New)**: While the task is running, if it is reporting progress, the server responds with a custom progress object.
    ```json
    {
      "root": {
        "title": "progress",
        "percent": 25,
        "description": "Transcribing file 2 of 8..."
      }
    }
    ```
5.  **Final Result**: Once the job is finished, the polling endpoint responds with the final result as before.

---

## 3. Implementation Guide

Implementing this feature requires changes in three places: the Celery task itself, the `MLService` helper that serves the result, and the frontend client that displays the progress.

### Step 1: Report Progress from the Celery Task

The core of this feature is the task's ability to report its own progress. This is done using the `self.update_state()` method available on a bound Celery task.
refer : https://docs.celeryq.dev/en/stable/userguide/tasks.html or https://docs.celeryq.dev/en/stable/userguide/calling.html
and search for "update_state"

**Proposed Changes in**: `src/audio-transcription/audio_transcription/main.py`

```python
# The transcribe_task needs to be modified to calculate and report progress.
@shared_task(bind=True)
def transcribe_task(self, inputs: AudioInput) -> ResponseBody:
    logger.info(f"Task {self.request.id}: Starting async transcription.")
    
    dirpath = DirectoryPath(inputs["input_dir"].path)
    
    # --- Example Progress Reporting Logic ---
    audio_files = list(dirpath.glob("*.mp3")) # or other audio extensions
    total_files = len(audio_files)
    results = []

    for i, file_path in enumerate(audio_files):
        # 1. Update state with current progress
        percent_complete = int(((i + 1) / total_files) * 100)
        self.update_state(
            state='PROGRESS',
            meta={
                'percent': percent_complete,
                'description': f'Transcribing {file_path.name} ({i+1} of {total_files})'
            }
        )
        
        # Perform the actual work for one file
        result = model.transcribe_file(file_path)
        results.append({"result": result, "file_path": file_path})
    # --- End of Example ---

    result_texts = [
        TextResponse(value=r["result"], title=str(r["file_path"])) for r in results
    ]
    response = BatchTextResponse(texts=result_texts)
    
    logger.info(f"Task {self.request.id}: Async transcription finished.")
    return ResponseBody(root=response)
```

### Step 2: Expose Progress via the Polling Endpoint

The `get_result` function within `MLService` must be updated to recognize and return this new progress information.

**Proposed Changes in**: `src/rb-lib/rb/lib/ml_service.py`

First, a new Pydantic model for the progress response should be defined in `rb/api/models.py`:

```python
# In rb/api/models.py
class ProgressResponse(BaseModel):
    title: str = "progress"
    percent: int
    description: Optional[str] = None
```

Then, the `get_result` function in `MLService` should be updated:

```python
# In MLService.add_ml_service.<locals>.get_result
def get_result(task_id: str):
    result = AsyncResult(task_id, app=rb_celery_app)
    
    if result.ready():
        if result.successful():
            return result.get()
        else:
            return ResponseBody(root=TextResponse(value=f"Task failed: {result.info}", title="error"))
    # --- NEW: Handle Progress State ---
    elif result.state == 'PROGRESS':
        # If the task is in our custom PROGRESS state, return the metadata.
        return ResponseBody(
            root=ProgressResponse(
                percent=result.info.get('percent', 0),
                description=result.info.get('description', '')
            )
        )
    # --- End of New Code ---
    else:
        # Fallback for standard PENDING state.
        return ResponseBody(root=TextResponse(value=f"Task status: {result.state}", title="status"))
```

### Step 3: Display Progress on the Frontend

Finally, the client's polling function must be updated to handle the new `progress` response type.

**Proposed Changes in**: `web/rescuebox-autoui/src/App.jsx`

```javascript
const pollForResult = async (resultUrl) => {
    try {
        const resultResponse = await fetch(resultUrl, { method: "GET" });
        const resultData = await resultResponse.json();

        // --- NEW: Handle Progress Type ---
        if (resultData && resultData.root.title === "progress") {
            const { percent, description } = resultData.root;
            setCommandOutput(`In Progress: ${percent}% - ${description}`);
            // Poll again after a short delay to get the next update
            setTimeout(() => pollForResult(resultUrl), 2000); // 2-second delay
        }
        // --- End of New Code ---
        else if (resultData && resultData.root.title === "status" && resultData.root.value.includes("PENDING")) {
            setCommandOutput((prev) => prev + " .");
            setTimeout(() => pollForResult(resultUrl), 5000); // 5-second delay
        } else {
            // Task is done, display the final result
            setCommandOutput(JSON.stringify(resultData, null, 2));
            setIsPolling(false);
        }
    } catch (error) {
        setCommandOutput((prev) => prev + `\n Polling Error: ${error.message}`);
        setIsPolling(false);
    }
};
```
