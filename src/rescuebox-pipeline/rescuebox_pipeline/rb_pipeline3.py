from pathlib import Path
import sys
import time
from celery import chain
from celery.contrib.abortable import AbortableAsyncResult
from celery.exceptions import TimeoutError

# import the methods to use in the pipeline from worker file
from rb_celery import (
    app,
    run_audio_plugin,
    run_text_summarization_plugin,
)

"""
Example of a RescueBox pipeline using Celery tasks.
This script demonstrates the correct way to run a pipeline with a timeout
and handle cancellation from the client side, avoiding worker deadlocks.
"""

print("--- Starting Pipeline: Transcribe then Summarize ---")

# 1. Define paths and parameters
audio_mp3_path = Path.cwd() / "rescuebox_pipeline" / "audio"
output_summarize_path = Path.cwd() / "audio" / "summarize_output"
model_to_use = "llama3.2:3b"
timeout_seconds = 10

# 2. Create the individual task signatures for your pipeline
task1_signature = run_audio_plugin.s(path=audio_mp3_path)
# The signature for the second task must be constructed to accept the output of the first task (`inpath`).
task2_signature = run_text_summarization_plugin.s(
    inputs={"output_dir": str(output_summarize_path)}, 
    parameters={"model_name": model_to_use},
)

# 3. Create the pipeline chain
pipeline_chain = chain(task1_signature, task2_signature)

# 4. Execute the pipeline asynchronously
pipeline_result = pipeline_chain.apply_async()

print(f"Pipeline started with ID: {pipeline_result.id}. Waiting for result with a {timeout_seconds}s timeout...")

# 5. Monitor the pipeline from the client, with timeout and cancellation logic
try:
    # This call will block until the result is ready OR the timeout is reached.
    final_outcome = pipeline_result.get(timeout=timeout_seconds)

    # This part of the code will only be reached if the pipeline succeeds
    if pipeline_result.successful():
        print("\n--- Pipeline Finished Successfully ---")
        print(f"Final Outcome: {final_outcome}")
        print(f"Final State: {pipeline_result.state}")
        if pipeline_result.parent:
            print("Audio transcribe output path: ", pipeline_result.parent.get())
        print("Text summarize output path: ", pipeline_result.get())

except TimeoutError:
    print(f"\n--- Pipeline Timed Out after {timeout_seconds} seconds ---")
    print("Revoking all tasks in the pipeline...")
    # Revoke the entire chain of tasks by traversing the parent hierarchy.
    # This is more robust than just revoking the final task.
    task_to_revoke = AbortableAsyncResult(pipeline_result.id, app=app)
    while task_to_revoke:
        print(f"Revoking task: {task_to_revoke.id}")
        task_to_revoke.abort()  # For AbortableTask
        app.control.revoke(task_to_revoke.id, terminate=True)  # Forcibly terminate
        task_to_revoke = task_to_revoke.parent
    print(f"Final State: {pipeline_result.state}")
    sys.exit(1)
except Exception as e:
    print(f"\n--- Pipeline Failed Unexpectedly ---")
    print(f"Caught unexpected exception: {type(e).__name__}: {e}")
    print(f"Final State: {pipeline_result.state}")
    sys.exit(1)