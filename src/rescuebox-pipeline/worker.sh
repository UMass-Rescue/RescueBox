# start celery worker from inside the container
# this will execute tasks run schedules from rb_pipeline.py , rb_pipeline2.py , rb_pipeline3.py
# when you run a demo.sh cmdline.

cd /home/rbuser/RescueBox/src/rescuebox-pipeline
poetry run celery -A rescuebox_pipeline.rb_celery  worker -l DEBUG --pool=solo
