# Logging Guide

## Overview

The RescueBox Desktop frontend uses Python's `logging` module with a contextual logging system that automatically includes job IDs, model IDs, and session IDs in all log messages. This enables precise log filtering and correlation for debugging and audit purposes.

## Contextual Logging System

### What is Contextual Logging?

Contextual logging automatically adds contextual information (job_id, model_id, session_id) to every log message. This allows you to:

- Filter logs by specific job or model
- Track all logs related to a specific execution
- Generate audit trails with job-specific logs
- Debug issues by correlating logs across components

### Log Format

All log messages follow this structured format:

```
{timestamp} | {level} | job_id={job_id} | model_id={model_id} | session_id={session_id} | {logger_name} | {message}
```

Example:
```
2024-01-15 14:30:45 | INFO     | job_id=abc123 | model_id=model456 | session_id=session789 | frontend.pages.chatbot.chatbot_handlers | Job abc123 created in database
```

If a context ID is not set, it appears as `-`:
```
2024-01-15 14:30:45 | INFO     | job_id=- | model_id=- | session_id=- | frontend.main | Application started
```

## Usage

### Setting Logging Context

Use `set_logging_context()` to set contextual information for the current execution context:

```python
from frontend.utils.logging_context import set_logging_context

# Set context for a job
set_logging_context(
    job_id='job_123',
    model_id='model_456',
    session_id='session_789'
)

# All subsequent log messages will include these IDs
logger.info("Processing job")
```

### Getting Current Context

Retrieve the current logging context:

```python
from frontend.utils.logging_context import get_logging_context

context = get_logging_context()
# Returns: {'job_id': 'job_123', 'model_id': 'model_456', 'session_id': 'session_789'}
```

### Clearing Context

Clear the logging context:

```python
from frontend.utils.logging_context import clear_logging_context

clear_logging_context()
```

## Automatic Context Setting

The logging context is automatically set when jobs are created:

### Job Creation

When a job is created via the chatbot handler (`frontend/pages/chatbot/chatbot_handlers.py`):

1. Job is created in the database
2. Logging context is set with:
   - `job_id`: The created job's UID
   - `model_id`: The model UID (if available)
   - `session_id`: The conversation ID from NiceGUI storage

Example:
```python
# Job is created
job = await job_db.create_job(...)

# Context is automatically set
set_logging_context(
    job_id=job.uid,
    model_id=model_uid,
    session_id=conversation_id
)
```

### Context Propagation

The logging context uses Python's `contextvars`, which means:

- **Thread-safe**: Each thread has its own context
- **Async-safe**: Each async task has its own context
- **Automatic**: Context propagates through function calls
- **Isolated**: Context doesn't leak between different executions

## Configuration

### Log File Location

Logs are written to: `frontend/data/rescuebox.log`

This can be configured in `frontend/config.py`:

```python
LOG_FILE = DATA_DIR / 'rescuebox.log'
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Logging Setup

Logging is configured at application startup in `frontend/main.py`:

```python
from frontend.utils.logging_context import configure_logging_with_context
from frontend.config import LOG_FILE, LOG_LEVEL

# Configure root logger with context filter and file handler
configure_logging_with_context(log_file_path=str(LOG_FILE), log_level=LOG_LEVEL)
```

This configuration:

1. Sets up console and file handlers
2. Adds the `ContextFilter` to include IDs in log records
3. Configures the log format with contextual information
4. Sets the log level (default: INFO)

## Reading and Filtering Logs

### Reading Logs by ID

Use `read_logs_filtered()` to read logs filtered by contextual IDs:

```python
from frontend.utils.log_reader import read_logs_filtered

# Read logs for a specific job
logs = await read_logs_filtered(job_id='job_123')

# Read logs matching multiple IDs
logs = await read_logs_filtered(
    job_id='job_123',
    model_id='model_456',
    session_id='session_789'
)
```

### Time-Based Filtering

Filter logs by time range:

```python
from datetime import datetime

logs = await read_logs_filtered(
    job_id='job_123',
    start_time=datetime(2024, 1, 15, 14, 0, 0),
    end_time=datetime(2024, 1, 15, 15, 0, 0)
)
```

### Log Entry Structure

Each log entry is a dictionary with:

```python
{
    'timestamp': datetime(2024, 1, 15, 14, 30, 45),
    'level': 'INFO',
    'job_id': 'job_123',
    'model_id': 'model_456',
    'session_id': 'session_789',
    'logger': 'frontend.pages.chatbot.chatbot_handlers',
    'message': 'Job job_123 created in database',
    'raw': '2024-01-15 14:30:45 | INFO | job_id=job_123 | ...'
}
```

## Integration with Audit Trails

The contextual logging system is integrated with audit trails:

1. **Job Creation**: Context is set automatically
2. **Logging**: All logs include contextual IDs
3. **Audit Trail Generation**: Logs are filtered by job_id and model_id
4. **Export**: Filtered logs are included in the audit trail

See [Audit Trail Guide](AUDIT_TRAIL_GUIDE.md) for more information.

## Best Practices

### Setting Context Early

Set logging context as early as possible in your execution flow:

```python
# Good: Set context immediately after job creation
job = await job_db.create_job(...)
set_logging_context(job_id=job.uid, ...)

# Bad: Set context much later
job = await job_db.create_job(...)
# ... many operations ...
set_logging_context(job_id=job.uid, ...)  # Too late!
```

### Including All Relevant IDs

Include all relevant IDs when setting context:

```python
# Good: Include all available IDs
set_logging_context(
    job_id=job.uid,
    model_id=model_uid,  # If available
    session_id=conversation_id  # If available
)

# Less ideal: Only job_id
set_logging_context(job_id=job.uid)
```

### Context Scope

Be aware of context scope:

- Context persists for the entire execution context (function call, async task, etc.)
- Context does not persist across different requests or sessions
- Each new execution starts with empty context (all IDs are None)

## File Locations

- **Context Management**: `frontend/utils/logging_context.py`
- **Log Reader**: `frontend/utils/log_reader.py`
- **Configuration**: `frontend/config.py`
- **Setup**: `frontend/main.py`

## Troubleshooting

### Logs Not Including IDs

If logs don't include IDs:

1. **Check if context is set**: Use `get_logging_context()` to verify
2. **Check log format**: Ensure `ContextFilter` is added to handlers
3. **Check timing**: Context must be set before logging

### Logs Not Found in Filtering

If filtering doesn't find expected logs:

1. **Verify IDs match**: Check that job_id, model_id, session_id are correct
2. **Check time range**: Ensure logs fall within the specified time range
3. **Check log file**: Verify logs are being written to the expected file
4. **Check log format**: Ensure logs match the expected format

### Context Not Persisting

If context doesn't persist:

1. **Check contextvars**: Context uses `contextvars`, which are isolated per execution context
2. **Check async tasks**: Each async task has its own context
3. **Check threads**: Each thread has its own context

## Related Documentation

- [Audit Trail Guide](AUDIT_TRAIL_GUIDE.md) - Using logs in audit trails
- [Job Database](database/README.md) - Job storage and retrieval
- [Chat History](CHAT_HISTORY_README.md) - Conversation management
