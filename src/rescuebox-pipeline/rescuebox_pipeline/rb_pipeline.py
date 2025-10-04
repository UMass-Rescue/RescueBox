from pathlib import Path
import time
from celery.result import AsyncResult
from celery import chain
from rb_celery import app
from rb_celery import run_audio_plugin
from rb_celery import run_text_summarization_plugin

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

audio_mp3_path = Path.cwd() / "rescuebox_pipeline" / "audio"
output_summarize_path = Path.cwd() / "src" / "rescuebox-pipeline" / "rescuebox_pipeline" / "summarize_output"
# paramete for summarize plugin
model_to_use = "llama3.2:3b"

# chain two plugins
result = chain(
    run_audio_plugin.s(audio_mp3_path), run_text_summarization_plugin.s(
        inputs={"output_dir": str(output_summarize_path)},
        parameters={"model_name": model_to_use})
)()

check_status(result.id)

try:
    print("first method in pipeline audio transcribe output= ", result.parent.get())
    print("second method in pipeline text summarize output= ", result.get())
except Exception as e:
    print("Task error occurred:", e)
