from pathlib import Path
import sys
from rescue_box_api_client import Client
from rescue_box_api_client.models import BatchTextResponse
from rescue_box_api_client.api.manage import list_plugins_post

from rescue_box_api_client.api.audio import (
    rb_audio_api_app_metadata_get,
)

from rescue_box_api_client.api.audio import rb_audio_api_routes_get

from rescue_box_api_client.api.audio import (
   rb_audio_transcribe_task_schema_get,
)

from rescue_box_api_client.api.audio import rb_audio_transcribe_post
from rescue_box_api_client.models.audio_directory import AudioDirectory
from rescue_box_api_client.models.audio_input import AudioInput
from rescue_box_api_client.models.body_audio_transcribe_post import (
    BodyAudioTranscribePost,
)
from rescue_box_api_client.models.directory_input import DirectoryInput
from rescue_box_api_client.models.validation_error import ValidationError


from rescue_box_api_client.api.text_summarization import (
    rb_text_summarization_api_app_metadata_get,
)
from rescue_box_api_client.api.text_summarization import (
    rb_text_summarization_api_routes_get,
)
from rescue_box_api_client.api.text_summarization import (
    rb_text_summarization_summarize_task_schema_get,
)
from rescue_box_api_client.api.text_summarization import (
    rb_text_summarization_summarize_post,
)
from rescue_box_api_client.models.body_text_summarization_summarize_post import (
    BodyTextSummarizationSummarizePost,
)
from rescue_box_api_client.models.inputs_2 import Inputs2

from rescue_box_api_client.models.parameters import Parameters


# assume rescuebox  run_server is up and running on port 8000
# create client and run the audio plugin api calls

client = Client(base_url="http://localhost:8000", verify_ssl=False)

list_plugins_manage_list_plugins_post = list_plugins_post.sync(
    client=client,
    streaming=False,
)
print("list plugins", list_plugins_manage_list_plugins_post)


field_audio_api_app_metadata_audio_api_app_metadata_get = (
    rb_audio_api_app_metadata_get.sync(
        client=client,
        streaming=False,
    )
)
print("audio app_metadata", field_audio_api_app_metadata_audio_api_app_metadata_get)

rb_audio_api_routes_get = (
    rb_audio_api_routes_get.sync(
        client=client,
        streaming=False,
    )
)
print("audio routes", rb_audio_api_routes_get)

rb_audio_transcribe_task_schema_get = (
    rb_audio_transcribe_task_schema_get.sync(
        client=client,
        streaming=False,
    )
)
print(
    "audio schema", rb_audio_transcribe_task_schema_get
)

try:
    bad_path = Path.cwd()
    good_path = Path.cwd() / ".." / "src" / "audio-transcription" / "tests"

    transcribe_out = rb_audio_transcribe_post.sync(
        client=client,
        streaming=False,
        body=BodyAudioTranscribePost(
            inputs=AudioInput(
                input_dir=AudioDirectory(path=str(good_path)),
            ),
        ),
    )
    if isinstance(transcribe_out, ValidationError):
        print("audio transcribe error ", transcribe_out)
    if isinstance(transcribe_out, BatchTextResponse) and len(transcribe_out.texts) > 0:
        data = transcribe_out.texts[0].value
        print("audio transcribe output text ", data)
        text_out_path = Path.cwd() / ".." / "src" / "text-summary" / "audio_summary"
        with open(
            text_out_path / "text_audio_output.txt", "w"
        ) as f:
            f.write(data)
        print("text summarization output written to file")
    else:
        raise Exception(
            f"audio transcribe failed {transcribe_out}"
        )
except Exception as e:
    print("audio transcribe error", e)
    sys.exit(1)


rb_text_summarization_api_app_metadata_get = rb_text_summarization_api_app_metadata_get.sync(
    client=client,
    streaming=False,
)
print(
    "text summarization app_metadata",
    rb_text_summarization_api_app_metadata_get,
)
rb_text_summarization_api_routes_get = (
    rb_text_summarization_api_routes_get.sync(
        client=client,
        streaming=False,
    )
)
print(
    "text summarization routes",
    rb_text_summarization_api_routes_get,
)
rb_text_summarization_task_schema_get = rb_text_summarization_summarize_task_schema_get.sync(
    client=client,
    streaming=False,
)
print(
    "text summarization schema",
    rb_text_summarization_task_schema_get,
)


try:
    text_path = Path.cwd() / ".." / "src" / "text-summary" / "test_input"
    text_in_path = Path.cwd() / ".." / "src" / "text-summary" / "audio_summary"

    text_out_path = Path.cwd() /  ".." / "src" / "text-summary" / "audio_summary" / "output"
    text_out_path.mkdir(parents=True, exist_ok=True)
    text_summarization_out = (
        rb_text_summarization_summarize_post.sync(
            client=client,
            streaming=False,
            body= BodyTextSummarizationSummarizePost(
                inputs=Inputs2(
                    input_dir=DirectoryInput(path=str(text_in_path)),
                    output_dir=DirectoryInput(path=str(text_out_path)),
                ),
                parameters=Parameters(
                    model="llama3.2:3b",
                ),
            ),
        )
    )

    if isinstance(text_summarization_out, ValidationError):
        print("text summarization error ", text_summarization_out)
    if (
        isinstance(text_summarization_out, BatchTextResponse)
        and len(text_summarization_out.texts) > 0
    ):
        data = text_summarization_out.texts[0].value
        print("text summarization output text ", data)
       
except Exception as e:
    print("text summarization error", e)
