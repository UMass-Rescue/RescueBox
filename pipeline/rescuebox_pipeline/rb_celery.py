from pathlib import Path
import time
from celery import Celery, shared_task, states
from celery.signals import task_prerun
from celery.exceptions import Ignore
from celery.contrib.abortable import AbortableTask
from celery.contrib.abortable import AbortableAsyncResult
from celery import chain
from rescue_box_api_client import Client
from rescue_box_api_client.models import BatchTextResponse
from rescue_box_api_client.api.manage import list_plugins_post


from rescue_box_api_client.api.audio import rb_audio_transcribe_post
from rescue_box_api_client.models.audio_directory import AudioDirectory
from rescue_box_api_client.models.audio_input import AudioInput
from rescue_box_api_client.models.body_audio_transcribe_post import (
    BodyAudioTranscribePost,
)
from rescue_box_api_client.models.directory_input import DirectoryInput
from rescue_box_api_client.models.validation_error import ValidationError


from rescue_box_api_client.api.text_summarization import (
    rb_text_summarization_summarize_post,
)
from rescue_box_api_client.models.body_text_summarization_summarize_post import (
    BodyTextSummarizationSummarizePost,
)
from rescue_box_api_client.models.text_summarization_summarize_inputs import (
    TextSummarizationSummarizeInputs,
)

from rescue_box_api_client.models.text_summarization_summarize_parameters import (
    TextSummarizationSummarizeParameters,
)

# broker="sqla+sqlite:///celerydb.db",
# broker='pyamqp://guest@localhost//'
# result_backend="db+sqlite:///broker.db",

# backend="rpc://" -if this is used abort/revoke does not work as expected

app = Celery(
    "rb_celery",
    broker="pyamqp://guest@localhost//",
    result_backend="db+sqlite:///broker.db",
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

list_plugins_manage_list_plugins_post = list_plugins_post.sync(
    client=client,
    streaming=False,
)
if not list_plugins_manage_list_plugins_post:
    print("no plugins found, please check the rescuebox server is running on port 8000")


@shared_task(bind=True)
def save_text_to_file(data: str, out_path: Path) -> Path:
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


@app.task
def run_audio_plugin_get_text(path: Path) -> str:
    file_path = run_audio_plugin.apply(args=[path]).get()
    print("read from file_path ", file_path)
    try:
        files = file_path.glob("*.txt")
        text_file = ""
        for file in files:
            print("file name ", file)
            text_file = file
        print("read text file ", text_file)
        with open(text_file, "r") as f:
            txt = f.read()
            print("text length ", len(txt))
            return txt
    except Exception as e:
        print("file read error", e)
    return None


@shared_task(bind=True, base=AbortableTask)
def run_audio_plugin(self, path: Path) -> Path:

    good_path = Path.cwd() / "audio"
    if path.exists():
        good_path = path

    transcribe_out = rb_audio_transcribe_post.sync(
        client=client,
        streaming=False,
        body=BodyAudioTranscribePost(
            inputs=AudioInput(
                input_dir=AudioDirectory(path=str(good_path)),
            ),
        ),
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
        raise Exception(f"audio transcribe failed {transcribe_output}")
    return text_out_path.resolve()


# define a custom exception for clarity
class PipelineCancelledError(Exception):
    """Custom exception for when a pipeline is cancelled by the client."""

    pass


# The watcher task runs tasks in chain and handles timeouts and sets the final state.
# user cancels this chain-task and it in turn revokes + aborts sub tasks
@shared_task(bind=True, base=AbortableTask)
def run_pipeline_with_timeout(self, pipeline_tasks: list, timeout: int = 50):
    """
    A "watcher" task that executes a pipeline chain and enforces a timeout.
    If the pipeline times out, this task revokes the chain and marks its own state as FAILURE.
    """
    print(f"Received pipeline_tasks: {pipeline_tasks}")

    pipeline_chain = chain(*pipeline_tasks)

    print("Applying chain...")
    pipeline_async_result = pipeline_chain.apply_async()
    print(f"Chain applied. Result ID: {pipeline_async_result.id}")

    time_elapsed = 0
    print(pipeline_async_result)

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
    return pipeline_async_result.get()


@shared_task(bind=True, base=AbortableTask)
def run_text_summarization_plugin(
    self, inpath: Path, outpath: Path, model_name: str = "llama3.2:3b"
) -> Path:
    # --- Add this line for debugging ---
    print(f"DEBUG: text_summarization received args: {locals()}")

    text_in_path = inpath
    if inpath.exists():
        text_in_path = inpath.resolve()
    text_out_path = outpath
    text_out_path.mkdir(parents=True, exist_ok=True)
    text_out_path = outpath.resolve()
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
    return text_out_path.resolve()
