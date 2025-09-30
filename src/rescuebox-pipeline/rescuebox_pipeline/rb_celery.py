from pathlib import Path
import time
import json

from typing import Any
from celery import Celery, shared_task
from celery.signals import task_prerun
from celery.exceptions import Ignore, TimeoutError
from celery.contrib.abortable import AbortableTask
from celery.contrib.abortable import AbortableAsyncResult
from celery import chain
# import sibling rb modules
import os, sys
sys.path.append(os.path.abspath('../'))
sys.path.append(os.path.abspath('../rescue-box-api-client'))
sys.path.append(os.path.abspath('../rb-api'))
sys.path.append(os.path.abspath('../rb-lib'))
sys.path.append(os.path.abspath('../audio-transcription'))
sys.path.append(os.path.abspath('./rescuebox_pipeline'))


from rescue_box_api_client import (
    Client
)
from rescue_box_api_client.models import (
    TextSummarizationSummarizeInputs,
    TextSummarizationSummarizeParameters, 
    DirectoryInput,
    BatchTextResponse
)

from  rescue_box_api_client.api.manage import list_plugins_post


from rescue_box_api_client.api.audio import rb_audio_transcribe_post
from rescue_box_api_client.models.audio_directory import AudioDirectory
from rescue_box_api_client.models.audio_input import AudioInput
from rescue_box_api_client.models.body_audio_transcribe_post import (
    BodyAudioTranscribePost,
)
from rescue_box_api_client.models.validation_error import ValidationError


from rescue_box_api_client.api.text_summarization import (
    rb_text_summarization_summarize_post,
)
from rescue_box_api_client.models.body_text_summarization_summarize_post import (
    BodyTextSummarizationSummarizePost,
)

# broker="sqla+sqlite:///celerydb.db",
# broker='pyamqp://guest@localhost//'
# result_backend="db+sqlite:///broker.db",

# backend="rpc://" -if this is used abort/revoke does not work as expected

app = Celery(
    "rb_celery",
    broker="pyamqp://guest@localhost//",
    result_backend="file://c:/work/rel/RescueBox/results/",
    result_extended=True,
    include=["audio-transcription.audio_transcription.main"] # must add every plugin's main that defines a @shared_task
)

# this is the default serializer for chain method args Path object
app.conf.task_serializer = "pickle"
app.conf.result_serializer = "pickle"
app.conf.accept_content = ["application/json", "application/x-python-serialize"]

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

WORKER_NAME = "celery@rb_worker"


@task_prerun.connect()
def log_celery_task_call(task, *args, **kwargs):
    print(f"{task.name} {args=} {kwargs=}")


# assume rescuebox  run_server is up and running on port 8000
# create client and run the audio plugin api calls

client = Client(base_url="http://localhost:8000", verify_ssl=False)


@shared_task(bind=True, base=AbortableTask, name="rescuebox_pipeline.rb_celery.save_text_to_file")
def save_text_to_file(self, data: str, out_path: Path) -> Path:
    try:
        file_path = out_path.resolve()
        file_out_path = file_path.parent
        file_out_path.mkdir(parents=True, exist_ok=True)
        print("file save path ", file_out_path)
        with open(file_path, "w") as f:
            f.write(data)
        print("file saved to ", file_path)
    except Exception as e:
        print("file save error", e)
    return file_out_path


@app.task(bind=True, base=AbortableTask,
          name="rescuebox_pipeline.rb_celery.run_audio_plugin_get_text")
def run_audio_plugin_get_text(self, path: Path) -> str:
    good_path = Path.cwd() / "rescuebox_pipeline" / "audio"
    if path.exists():
        good_path = path

    # Construct the request body object to inspect it before sending.
    request_body = BodyAudioTranscribePost(
        inputs=AudioInput(
            input_dir=AudioDirectory(path=str(good_path.resolve()))
        ),
    )

    # Log the dictionary representation of the request body.
    print(f"DEBUG: Sending POST request to /audio/transcribe with body:\n{json.dumps(request_body.to_dict(), indent=2)}")

    transcribe_out = rb_audio_transcribe_post.sync(
        client=client,
        streaming=False,
        body=request_body,
    )

    if self.is_aborted():
        raise Ignore()

    if isinstance(transcribe_out, ValidationError):
        print("audio transcribe error ", transcribe_out)
    if isinstance(transcribe_out, BatchTextResponse) and len(transcribe_out.texts) > 0:
        data = transcribe_out.texts[0].value
        print(f"audio transcribe output text {len(data)}")
        return data


@shared_task(bind=True, base=AbortableTask,
             name="rescuebox_pipeline.rb_celery.run_audio_plugin")
def run_audio_plugin(self, path: Path) -> Path:

    good_path = Path.cwd() / "rescuebox_pipeline" / "audio"
    if path.exists():
        good_path = path

    # Construct the request body object to inspect it before sending.
    request_body = BodyAudioTranscribePost(
        inputs=AudioInput(
            input_dir=AudioDirectory(path=str(good_path.resolve()))
        ),
    )

    # Log the dictionary representation of the request body.
    print(f"DEBUG: Sending POST request to /audio/transcribe with body:\n{json.dumps(request_body.to_dict(), indent=2)}")

    transcribe_out = rb_audio_transcribe_post.sync(
        client=client,
        streaming=False,
        body=request_body,
    )

    if self.is_aborted():
        raise Ignore()

    if isinstance(transcribe_out, ValidationError):
        print("audio transcribe error ", transcribe_out)
    if isinstance(transcribe_out, BatchTextResponse) and len(transcribe_out.texts) > 0:
        data = transcribe_out.texts[0].value
        print("audio transcribe output text ", data)
        text_out_path = Path.cwd() / "audio" / "transcribe_output"
        text_out_path.mkdir(parents=True, exist_ok=True)
        text_out_file = text_out_path / "audio.txt"
        with open(text_out_file, "w") as f:
            f.write(data)
        print("audio text output written to file")

    else:
        raise Exception(f"audio transcribe failed {transcribe_out}")
    return text_out_path.resolve()


# define a custom exception for clarity
class PipelineCancelledError(Exception):
    """Custom exception for when a pipeline is cancelled by the client."""

    pass


# this is not working as expected on windows
# reason seems to be deadlock between task result and execution
# run_pipeline_with_timeout_list works on windows using filesystem as result-backend
# TODO : need to run this on mac and make it work
@shared_task(bind=True, base=AbortableTask,
             name="rescuebox_pipeline.rb_celery.run_pipeline_with_timeout")
def run_pipeline_with_timeout(self, pipeline_tasks_id: str, timeout: int = 20):
    """
    A "watcher" task that monitors a pipeline chain and enforces a timeout.
    If the pipeline times out, this task revokes the chain and marks its own state as FAILURE.
    """
    pipeline_async_result = AbortableAsyncResult(pipeline_tasks_id, app=app)

    time_elapsed = 0
    # Poll for the result in a non-blocking way.
    while not pipeline_async_result.ready():
        # Check if the watcher task itself has been aborted.
        if self.is_aborted():
            print(
                f"Watcher {self.request.id}: Aborted by client. Revoking sub-pipeline..."
            )
            # Revoke the entire chain of tasks.
            subtask_to_revoke = pipeline_async_result
            while subtask_to_revoke:
                print(f"Revoke+Abort task: {subtask_to_revoke.id}")
                app.control.revoke(subtask_to_revoke.id, terminate=True)
                abortable_result = AbortableAsyncResult(subtask_to_revoke.id, app=app)
                abortable_result.abort()
                subtask_to_revoke = subtask_to_revoke.parent
            # Raise a custom exception to indicate cancellation.
            raise PipelineCancelledError("Pipeline was cancelled by the client.")
        if time_elapsed >= timeout:
            print(
                f"Watcher {self.request.id}: Pipeline timed out after {timeout} seconds. Revoking sub-pipeline..."
            )
            # ... (revoke logic remains the same) ...
            subtask_to_revoke = pipeline_async_result
            while subtask_to_revoke:
                print(f"Revoke+Abort task: {subtask_to_revoke.id}")
                app.control.revoke(subtask_to_revoke.id, terminate=True)
                abortable_result = AbortableAsyncResult(subtask_to_revoke.id, app=app)
                abortable_result.abort()
                subtask_to_revoke = subtask_to_revoke.parent
            # Raise an exception to mark the watcher as FAILED
            raise TimeoutError(f"Pipeline timed out after {timeout}s")
        # Wait for 1 second before polling again
        time.sleep(1)
        time_elapsed += 1
    # If the loop exits, the pipeline is ready and finished successfully
    print(f"Watcher {self.request.id}: Pipeline completed successfully.")
    return pipeline_async_result


# The watcher task runs tasks in chain and handles timeouts and sets the final state.
# user cancels this chain-task and it in turn revokes + aborts sub tasks
@shared_task(bind=True, base=AbortableTask)
def run_pipeline_with_timeout_list(self, pipeline_tasks: list, initial_arg: Any, timeout: int = 50):
    """
    A "watcher" task that starts a pipeline chain and returns the AsyncResult for that chain.
    It does NOT wait for the result, to avoid deadlocks.
    """
    print(f"Watcher task received pipeline_tasks: {pipeline_tasks}")

    pipeline_chain = chain(*pipeline_tasks)

    print("Applying chain asynchronously...")
    # Start the chain and return its result object.
    pipeline_async_result = pipeline_chain.apply_async(args=[initial_arg])
    print(f"Returning chain result for id: {pipeline_async_result.id}")
    
    return pipeline_async_result.id


@shared_task(bind=True, base=AbortableTask,
             name="rescuebox_pipeline.rb_celery.run_text_summarization_plugin")
def run_text_summarization_plugin(
    self, inpath: Path, inputs: dict, parameters: dict
) -> Path:
    # --- Add this line for debugging ---
    print(f"DEBUG: text_summarization received args: {locals()}")

    text_in_path = inpath
    if inpath.exists():
        text_in_path = inpath.resolve()
    text_out_path = Path.cwd() / inputs.get("output_dir")
    text_out_path.mkdir(parents=True, exist_ok=True)
    print(f"text_out_path debug {text_out_path.resolve()}")
    model_name = parameters.get("model_name", "llama3.2:3b")
    text_summarization_out = rb_text_summarization_summarize_post.sync(
        client=client,
        streaming=False,
        body=BodyTextSummarizationSummarizePost(
            inputs=TextSummarizationSummarizeInputs(
                input_dir=DirectoryInput(path=str(text_in_path)),
                output_dir=DirectoryInput(path=str(text_out_path)),
            ),
            parameters=TextSummarizationSummarizeParameters(
                model=model_name,
            ),
        ),
    )
    if self.is_aborted():
        raise Ignore()

    if isinstance(text_summarization_out, ValidationError):
        print("text summarization error ", text_summarization_out)
    if (
        isinstance(text_summarization_out, BatchTextResponse)
        and len(text_summarization_out.texts) > 0
    ):
        data = text_summarization_out.texts[0].value
        print("text summarization output text ", data)
    print(f"Task {self.request.id} completed with result: {text_out_path.resolve()}")
    return text_out_path.resolve()
