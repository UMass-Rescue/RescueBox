

# demo diagram
https://derlin.github.io/introduction-to-fastapi-and-celery/03-celery/

cd C:\work\RescueBox

# start RB server
poetry run python -m src.rb-api.rb.api.main


cd C:\work\misc\new\RescueBox\sdk2

# start celery server
celery -A rb_celery  worker -l DEBUG --pool=solo


# run pipeline
python rb_pipeline.py
debug ["fs", "docs", "audio", "age-gender", "text_summarization"]
debug <class 'list'>
list plugins ['fs', 'docs', 'audio', 'age-gender', 'text_summarization']
first transcribe  , then summarize
first method audio output=  C:\work\misc\new\RescueBox\sdk2\..\src\text-summary\audio_summary
second methond summarize output=  C:\work\misc\new\RescueBox\sdk2\..\src\text-summary\audio_summary\output
