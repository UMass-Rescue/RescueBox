from pathlib import Path
from celery.result import AsyncResult
from celery import chain
from celery.contrib.abortable import AbortableAsyncResult
from rb_celery import (
    run_audio_plugin_get_text,
    save_text_to_file,
    run_text_summarization_plugin,
)
""" 
The goal of this code is to create a more granular pipeline:

run_audio_plugin_get_text: Transcribes the audio returns the raw text as a string in memory 
(instead of saving a file).
save_text_to_file: Takes the text string from the previous step and saves it to a specified file.
run_text_summarization_plugin: Takes the path to the newly created text file and runs 
summarization on it. this plugin outputs to a specified directory.
"""

print("")
print("-----------------------------------")
print("first transcribe -> save text to file -> then summarize")

audio_mp3_path = Path.cwd() / "audio"


intermediate_text_path = Path.cwd() / "audio" / "transcribe_output_2"

output_summarize_path = Path.cwd() / "audio" / "summarize_output_2"
# paramete for summarize plugin
model_to_use = "llama3.2:3b"

result = chain(
    run_audio_plugin_get_text.s(path=audio_mp3_path),
    save_text_to_file.s(out_path=intermediate_text_path),
    run_text_summarization_plugin.s(
        outpath=output_summarize_path, model_name=model_to_use
    ),
)()

print("first method in pipeline audio transcribe output= ", result.parent.parent.get())

print("second method in pipeline save text output= ", result.parent.get())

print("third methond in pipeline text summarize output= ", result.get())
