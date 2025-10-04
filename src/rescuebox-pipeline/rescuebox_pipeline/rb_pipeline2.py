from pathlib import Path
import time
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

audio_mp3_path = Path.cwd() / "rescuebox_pipeline" / "audio"


intermediate_text_path = Path.cwd() / "src" / "rescuebox-pipeline" / "rescuebox_pipeline" / "audio" / "transcribe_output_2" / "intermediate.txt"

output_summarize_path = Path.cwd() / "src" / "rescuebox-pipeline" / "rescuebox_pipeline" / "audio" / "summarize_output_2"
# paramete for summarize plugin
model_to_use = "llama3.2:3b"

result = chain(
    run_audio_plugin_get_text.s(path=audio_mp3_path),
    save_text_to_file.s(intermediate_text_path),
    run_text_summarization_plugin.s( # The output from the previous task will be the first argument (`inpath`).
        inputs={"output_dir": str(output_summarize_path)},
        parameters={"model_name": model_to_use},
    ),
)()


while not result.ready():
    time.sleep(1)

print("second method in pipeline (read_text_from_file) output= ", result.parent.get())


print("fourth method in pipeline (run_text_summarization_plugin) output= ", result.get())
