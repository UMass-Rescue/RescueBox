# generate sdk
curl --header "Content-Type: application/json" "http://localhost:8000/openapi.json"
save output to oo.json
openapi-python-client generate --path oo.json --output-path sdk2 --overwrite --config sdk_config.yaml
Generating sdk2

first : run celery worker
next  : run main.py

C:\work\misc\new\RescueBox\sdk\proj>python main.py
eab3f058-2544-496b-8da0-fc3681dcad4c
eab3f058-2544-496b-8da0-fc3681dcad4c


C:\work\misc\new\RescueBox\sdk\proj>

celery -A myapp  worker -l DEBUG --pool=solo


[2025-04-18 13:56:30,936: DEBUG/MainProcess] | Worker: Preparing bootsteps.
[2025-04-18 13:56:30,939: DEBUG/MainProcess] | Worker: Building graph...
[2025-04-18 13:56:30,939: DEBUG/MainProcess] | Worker: New boot order: {Timer, Hub, Pool, Autoscaler, StateDB, Beat, Consumer}
[2025-04-18 13:56:30,947: DEBUG/MainProcess] | Consumer: Preparing bootsteps.
[2025-04-18 13:56:30,947: DEBUG/MainProcess] | Consumer: Building graph...
[2025-04-18 13:56:30,996: DEBUG/MainProcess] | Consumer: New boot order: {Connection, Events, Mingle, Tasks, Control, Gossip, Agent, Heart, DelayedDelivery, event loop}

 -------------- celery@home-mini v5.5.1 (immunity)
--- ***** -----
-- ******* ---- Windows-11-10.0.22631-SP0 2025-04-18 13:56:30
- *** --- * ---
- ** ---------- [config]
- ** ---------- .> app:         myapp:0x1a3d28e4a40
- ** ---------- .> transport:   sqla+sqlite:///celerydb.db
- ** ---------- .> results:     sqlite:///broker.db
- *** --- * --- .> concurrency: 16 (solo)
-- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery


[tasks]
  . celery.accumulate
  . celery.backend_cleanup
  . celery.chain
  . celery.chord
  . celery.chord_unlock
  . celery.chunks
  . celery.group
  . celery.map
  . celery.starmap
  . myapp.get_hello

[2025-04-18 13:56:31,094: DEBUG/MainProcess] | Worker: Starting Pool
[2025-04-18 13:56:31,094: DEBUG/MainProcess] ^-- substep ok
[2025-04-18 13:56:31,094: DEBUG/MainProcess] | Worker: Starting Consumer
[2025-04-18 13:56:31,094: DEBUG/MainProcess] | Consumer: Starting Connection
[2025-04-18 13:56:31,112: INFO/MainProcess] Connected to sqla+sqlite:///celerydb.db
[2025-04-18 13:56:31,112: DEBUG/MainProcess] ^-- substep ok
[2025-04-18 13:56:31,112: DEBUG/MainProcess] | Consumer: Starting Events
[2025-04-18 13:56:31,112: DEBUG/MainProcess] ^-- substep ok
[2025-04-18 13:56:31,112: DEBUG/MainProcess] | Consumer: Starting Tasks
[2025-04-18 13:56:31,124: DEBUG/MainProcess] ^-- substep ok
[2025-04-18 13:56:31,124: DEBUG/MainProcess] | Consumer: Starting Heart
[2025-04-18 13:56:31,124: DEBUG/MainProcess] ^-- substep ok
[2025-04-18 13:56:31,124: DEBUG/MainProcess] | Consumer: Starting event loop
[2025-04-18 13:56:31,124: INFO/MainProcess] celery@home-mini ready.


[2025-04-18 13:56:31,124: DEBUG/MainProcess] basic.qos: prefetch_count->64
[2025-04-18 13:56:47,184: INFO/MainProcess] Task myapp.get_hello[eab3f058-2544-496b-8da0-fc3681dcad4c] received
[2025-04-18 13:56:47,184: DEBUG/MainProcess] TaskPool: Apply <function fast_trace_task at 0x000001A3D285A8E0> (args:('myapp.get_hello', 'eab3f058-2544-496b-8da0-fc3681dcad4c', {'lang': 'py', 'task': 'myapp.get_hello', 'id': 'eab3f058-2544-496b-8da0-fc3681dcad4c', 'shadow': None, 'eta': None, 'expires': None, 'group': None, 'group_index': None, 'retries': 0, 'timelimit': [None, None], 'root_id': 'eab3f058-2544-496b-8da0-fc3681dcad4c', 'parent_id': None, 'argsrepr': "('foo',)", 'kwargsrepr': '{}', 'origin': 'gen2524@home-mini', 'ignore_result': False, 'replaced_task_nesting': 0, 'stamped_headers': None, 'stamps': {}, 'properties': {'correlation_id': 'eab3f058-2544-496b-8da0-fc3681dcad4c', 'reply_to': '91bcba47-d39a-369d-b1ba-000a2c907a25', 'delivery_mode': 2, 'delivery_info': {'exchange': '', 'routing_key': 'celery'}, 'priority': 0, 'body_encoding': 'base64', 'delivery_tag': 'b56aac9b-a5e1-46f7-b4f4-7f262d2988ec'}, 'reply_to': '91bcba47-d39a-369d-b1ba-000a2c907a25', 'correlation_id': 'eab3f058-2544-496b-8da0-fc3681dcad4c', 'hostname': 'celery@home-mini', 'delivery_info': {'exchange': '', 'routing_key': 'celery', 'priority':... kwargs:{})


[2025-04-18 13:56:49,200: INFO/MainProcess] Task myapp.get_hello[eab3f058-2544-496b-8da0-fc3681dcad4c] succeeded in 2.016000000294298s: 'Hello foo'

--------------------------------------------------

https://stackoverflow.com/questions/45744992/celery-raises-valueerror-not-enough-values-to-unpack

Set an environment variable FORKED_BY_MULTIPROCESSING=1.
             Then you can simply run celery -A <celery module> worker.