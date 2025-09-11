from myapp import app
from myapp import get_hello
from celery.result import AsyncResult
import time



# pre create taskid , run task get status

task_id = '12340'  # uuid()
print(task_id)
result = get_hello.apply_async(args=["bar"],  task_id=task_id )

res = AsyncResult(task_id,app=app)
print("job status using id ", res.state) # 'PENDING'
# print("job output", res.get()) # blocking call

# PENDING
while not result.ready():
    print(f"Task status: {result.status}")
    time.sleep(1)  # Wait for a short duration before re-checking

# SUCCESS
if result.ready():
    print(f"Task result: {result.status} output:{result.get()}")
