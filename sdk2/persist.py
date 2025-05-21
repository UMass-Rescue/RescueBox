from myapp import app
from celery.result import AsyncResult

# get results of previously executed jobs with job id

# prev_id='37c487fb-f76e-4656-9770-e740d71400b8'


# res = AsyncResult(prev_id,app=app)

# print("job status", res.state) # 'SUCCESS'
# print("job output", res.get()) # 7



# pre create taskid 

task_id = uuid()
print(task_id)
result = get_hello.apply_async(args=["bar"],  task_id=task_id )

res = AsyncResult(task_id,app=app)

print("job output task_id", res.get()) # bar
