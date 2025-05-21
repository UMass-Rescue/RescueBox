from pathlib import Path
import time
from celery.result import AsyncResult
from celery import chain
from rb_celery import app
from rb_celery import run_audio_plugin
from rb_celery import run_text_summarization_plugin

# from rb_celery import  run_audio_plugin_get_text, save_text_to_file


def check_status(resid):
    res = AsyncResult(resid, app=app)
    count = 0
    while res.state == "PENDING":
        print("job status", resid, result.state)  # 'PENDING'
        time.sleep(3)
        count += 3
        res = AsyncResult(resid, app=app)
        print("job runtime=", count, " seconds")
        if count > 5:
            app.control.revoke(resid, terminate=True, signal="SIGKILL")


print("first transcribe -> then summarize")

audio_mp3_path = Path.cwd() / ".." / "src" / "audio-transcription" / "tests"

# chain two plugins
output_summarize_path = Path.cwd() / ".." / "src" / "text-summary" / "audio_summary" / "output"
result = chain(
    run_audio_plugin.s(audio_mp3_path), run_text_summarization_plugin.s(output_summarize_path)
)()

check_status(result.id)

print("first method in pipeline audio transcribe output= ", result.parent.get())
print("second methond in pipeline text summarize output= ", result.get())


# # first run audio plugin and get text output, instead of a file

# # second save text to a file

# # third pass this file to summarize along with output of summary folder 

# audio_text_path = Path.cwd() / ".." / "src" / "text-summary" / "audio_summary"  / "audio" /  "save_audio.txt"
# summarize_out_path = Path.cwd() / ".." / "src" / "text-summary" / "audio_summary"  / "output" 
# result = chain(run_audio_plugin_get_text.s(audio_path), save_text_to_file.s(audio_text_path), run_text_summarization_plugin.s(summarize_out_path))()


# check_status(result.id)

# print("first method in pipeline audio transcribe output= ", result.parent.parent.get())

# print("second method in pipeline save text output= ", result.parent.get())

# print("third methond in pipeline text summarize output= ", result.get())