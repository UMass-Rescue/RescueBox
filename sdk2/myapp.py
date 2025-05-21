from celery import Celery
from time import sleep
from celery.signals import task_prerun

#connect to local rabbitmq and db sqlite backend

# sqlite (filename)
# result_backend = 'db+sqlite:///db.sqlite3'

app=Celery('myapp', result_backend="db+sqlite:///broker.db",broker='sqla+sqlite:///celerydb.db')

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

@app.task
def add(x, y):
    return x + y


@app.task
def mul(x, y):
    return x * y


@app.task
def xsum(numbers):
    return sum(numbers)

@task_prerun.connect()
def log_celery_task_call(task, *args, **kwargs):
    print(f"{task.name} {args=} {kwargs=}")

@app.task #register task into celery app via decorator
def get_hello(name):
    sleep(12) #simulation for long running task
    retval = f"Hello {name}"
    return retval

if __name__ == '__main__':
    app.start()