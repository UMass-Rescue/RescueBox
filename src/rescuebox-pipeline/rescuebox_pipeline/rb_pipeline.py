from pathlib import Path
import time
from celery.result import AsyncResult
from celery import chain
from pipeline.rescuebox_pipeline.rb_celery import app
from pipeline.rescuebox_pipeline.rb_celery import run_audio_plugin
from pipeline.rescuebox_pipeline.rb_celery import run_text_summarization_plugin

# check task status
def check_status(resid):
    res = AsyncResult(resid, app=app)
    count = 0
    while res.state == "PENDING":
        print("job status", resid, result.state)  # 'PENDING'
        time.sleep(3)
        count += 3
        res = AsyncResult(resid, app=app)
        print("job runtime=", count, " seconds")
        if count > 50:
            app.control.revoke(resid, terminate=True)


print("first transcribe -> then summarize")

audio_mp3_path = Path.cwd() / "audio"
output_summarize_path = Path.cwd() / "audio" / "summarize_output"

# chain two plugins
result = chain(
    run_audio_plugin.s(audio_mp3_path), run_text_summarization_plugin.s(output_summarize_path)
)()

check_status(result.id)

try:
    print("first method in pipeline audio transcribe output= ", result.parent.get())
    print("second methond in pipeline text summarize output= ", result.get())
except Exception as e:
    print("Task error occurred:", e)
