import pytest
import threading
import time
from unittest.mock import MagicMock
from typing import Any, Dict, TypedDict
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rb.lib.ml_service import MLService
from rb.api.models import ResponseBody, TextResponse, TaskSchema

# Mock TaskSchema for the test
def mock_task_schema_func() -> TaskSchema:
    return TaskSchema(inputs=[], parameters=[])

class MockInputs(TypedDict):
    pass
class MockParameters(TypedDict):
    pass

class MockMLFunctionState:
    """Helper to track calls to the mock ML function."""
    def __init__(self):
        self.call_count = 0
        self.execution_log = []
        self.lock = threading.Lock()

    def reset(self):
        self.call_count = 0
        self.execution_log = []

mock_state = MockMLFunctionState()

def mock_ml_function(inputs: MockInputs, parameters: MockParameters) -> ResponseBody:
    """A mock ML function that simulates a time-consuming operation."""
    with mock_state.lock:
        mock_state.call_count += 1
        start_time = time.time()
        mock_state.execution_log.append(f"Start {threading.current_thread().name} at {start_time}")
        time.sleep(0.1)  # Simulate work
        end_time = time.time()
        mock_state.execution_log.append(f"End {threading.current_thread().name} at {end_time}")
        return TextResponse(value=f"Processed by {threading.current_thread().name}")

@pytest.fixture
def ml_service_with_lock():
    """Fixture to provide an MLService instance with a thread-safe function."""
    service_name = "test_locked_service"
    ml_service = MLService(service_name)
    ml_service.add_app_metadata(
        name="Test Locked Service",
        author="Test Author",
        version="1.0.0",
        info="A service to test thread locking.",
        plugin_name=service_name,
        make_threadsafe=True, # Explicitly set to True
    )
    ml_service.add_ml_service(
        rule="/process_locked",
        ml_function=mock_ml_function,
        inputs_cli_parser=MagicMock(),
        parameters_cli_parser=MagicMock(),
        task_schema_func=mock_task_schema_func,
        short_title="Process Locked",
        order=0,
    )
    mock_state.reset() # Reset state for each test
    
    yield ml_service

def test_ml_service_thread_lock_sequential_execution(ml_service_with_lock: MLService):
    """
    Tests that concurrent calls to a thread-safe ML function are executed sequentially.
    """
    ml_service = ml_service_with_lock
    endpoint_rule = f"/{ml_service.name}/process_locked"

    # Get the registered command callback
    run_cmd = next(cmd for cmd in ml_service.app.registered_commands if cmd.name == endpoint_rule)
    run_callback = run_cmd.callback

    num_concurrent_calls = 5
    threads = []
    results = []

    def make_request():
       try:
           response = run_callback(inputs={}, parameters={})
           results.append(200)
       except Exception:
           results.append(500)

    for i in range(num_concurrent_calls):
        thread = threading.Thread(target=make_request, name=f"TestThread-{i}")
        threads.append(thread)

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Assert all requests were successful
    assert all(res == 200 for res in results)
    assert mock_state.call_count == num_concurrent_calls

    # Verify sequential execution by checking timestamps
    # Each call takes 0.1s, so 5 sequential calls should take at least 0.5s
    # We sort the log entries by time and ensure that the 'End' time of one call
    # is not before the 'Start' time of the next call, indicating no overlap.
    
    # Parse the execution log to get start and end times for each call
    parsed_logs = []
    for log_entry in mock_state.execution_log:
        parts = log_entry.split(" ")
        action = parts[0]
        thread_name = parts[1]
        timestamp = float(parts[3])
        parsed_logs.append({"action": action, "thread": thread_name, "time": timestamp})

    # Group logs by thread and sort by time
    thread_executions = {}
    for entry in parsed_logs:
        thread_executions.setdefault(entry["thread"], []).append(entry)
    
    # Collect all start and end times, ensuring each thread has a start and end
    all_times = []
    for thread_name, entries in thread_executions.items():
        entries.sort(key=lambda x: x["time"])
        assert len(entries) == 2, f"Thread {thread_name} did not have a start and end log entry."
        assert entries[0]["action"] == "Start"
        assert entries[1]["action"] == "End"
        all_times.append((entries[0]["time"], entries[1]["time"]))
    
    # Sort by start time to check for overlaps
    all_times.sort(key=lambda x: x[0])

    # Check for overlaps: the end time of one should be less than or equal to the start time of the next
    for i in range(len(all_times) - 1):
        current_end = all_times[i][1]
        next_start = all_times[i+1][0]
        assert current_end <= next_start, f"Overlap detected between calls: {all_times[i]} and {all_times[i+1]}"

    # Optional: Print execution log for debugging if needed
    # print("\nExecution log:")
    # for entry in mock_state.execution_log:
    #     print(entry)