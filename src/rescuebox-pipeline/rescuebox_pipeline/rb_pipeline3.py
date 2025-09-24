from pathlib import Path
import sys
import time
from celery.result import AsyncResult
from celery import chain
from celery.contrib.abortable import AbortableAsyncResult

# import the methods to use in the pipeline from worker file
from rb_celery import (
    PipelineCancelledError,
    app,
    run_audio_plugin,
    run_audio_plugin_get_text,
    save_text_to_file,
    run_text_summarization_plugin,
    run_pipeline_with_timeout,
)

"""
Example of a RescueBox pipeline using Celery tasks
This example assumes you have a RescueBox server running locally on port 8000
and the Celery worker is also running.
"""

print("first transcribe -> then summarize")

audio_mp3_path = Path.cwd() / "audio"

# chain two plugins
output_summarize_path = Path.cwd() / "audio" / "summarize_output"
# paramete for summarize plugin
model_to_use = "llama3.2:3b"


# 1. Create the individual task signatures for your pipeline
task1_signature = run_audio_plugin.s(path=audio_mp3_path)
task2_signature = run_text_summarization_plugin.s(
    outpath=output_summarize_path, model_name=model_to_use
)

# 2. Put the signatures into a simple list
pipeline_as_list = [task1_signature, task2_signature]

# 2. Create the watcher task's signature, telling it to run our pipeline
watcher_signature = run_pipeline_with_timeout.s(
    pipeline_tasks=pipeline_as_list, timeout=20
)

# 3. Execute the watcher task
result = watcher_signature.apply_async()

abortable_result = AbortableAsyncResult(result.id, app=app)
print(f"Watcher task started with ID: {result.id}. Waiting for final result...")
# 4. Get the final result from the watcher
try:
    # 4. Simulate waiting for a short time before cancelling
    print("Pipeline is running. We will send a cancel request in 3 seconds...")
    time.sleep(3)

    # Call .abort() to cancel the AbortableTask
    print(f"Sending abort request to watcher task...{result.id}")
    abortable_result.abort()

    final_outcome = result.get()
except PipelineCancelledError as e:
    print("\n--- Pipeline Cancelled Successfully ---")
    print(f"Caught expected exception: {e}")
    print(f"Final State: {result.state}")  # Should be FAILURE
    sys.exit(1)
except Exception as e:
    print(f"\n--- Pipeline Failed Unexpectedly ---")
    print(f"Caught unexpected exception: {e}")
    print(f"Final State: {result.state}")
    sys.exit(1)

# This part of the code will only be reached if the pipeline succeeds
if result.successful():
    print("\n--- Pipeline Finished ---")
    print(f"Final Outcome: {final_outcome}")
    print(f"Final State: {result.state}")

# check_status(result)
if result.parent:
    print("first method in pipeline audio transcribe output= ", result.parent.get())
print("second methond in pipeline text summarize output= ", result.get())

