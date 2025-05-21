from myapp import add
from myapp import app
from celery.result import AsyncResult
from celery import  chain


'''
# simple task

print("start job get_hello('foo')")
result = get_hello.delay("foo")
print("job id", result.id)
resid = result.id

res = AsyncResult(resid,app=app)

print("job status", res.state) # 'SUCCESS'
print("job output", res.get()) # foo


'''

# chain add (1 +1 ) + (4)

print("first add 1 + 1, then add 4")
res = chain(add.s(1, 1), add.s(4))()

print ("first method 1 + 1 result = ", res.parent.get())

print("chain 2 + 4 = " , res.get())

lazy_chain = chain(add.s(i) for i in range(3))
print("lazy chain", lazy_chain)
res = lazy_chain(0)
print("lazy chain result =", res.get())
res = lazy_chain(4)
print("plus 4 lazy chain =", res.get())