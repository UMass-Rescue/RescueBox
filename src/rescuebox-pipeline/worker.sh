# start celery worker
# this will execute tasks run from rb_pipeline.py , rb_pipeline2.py , rb_pipeline3.py
cd src/rescuebox-pipeline
poetry run celery -A rescuebox_pipeline.rb_celery  worker -l DEBUG --pool=solo
