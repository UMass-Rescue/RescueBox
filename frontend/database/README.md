# Job Database Module

This module provides SQLite database functionality for storing and managing jobs in the RescueBox Desktop NiceGUI frontend. It mirrors the functionality from the Electron codebase, storing job information including model/task IDs, request/response data, and job status.

## Features

- **Job Storage**: All submitted jobs are automatically saved to a local SQLite database
- **Job Tracking**: Track job status (Running, Completed, Failed, Canceled)
- **Job History**: View all previous jobs sorted by start time
- **Job Details**: View complete job information including inputs, parameters, and results
- **Re-submission**: Re-submit jobs from the job details page
- **Flexible Support**: Supports both traditional jobs (with modelUid/taskUid) and chatbot jobs (with endpoint)

## Database Schema

The `jobs` table stores the following fields:

- `uid` (TEXT, PRIMARY KEY): Unique job identifier (UUID)
- `modelUid` (TEXT): Model unique identifier (optional, for traditional jobs)
- `taskUid` (TEXT): Task unique identifier (optional, for traditional jobs)
- `endpoint` (TEXT): API endpoint name (optional, for chatbot jobs)
- `startTime` (TEXT, NOT NULL): Job start time (ISO format)
- `endTime` (TEXT): Job end time (ISO format, optional)
- `status` (TEXT, NOT NULL): Job status (Running, Completed, Failed, Canceled)
- `statusText` (TEXT): Status text/message (optional)
- `request` (TEXT, NOT NULL): Request body as JSON string
- `response` (TEXT): Response body as JSON string (optional)
- `taskSchema` (TEXT, NOT NULL): Task schema at time of job creation as JSON string

## Usage

### Initialization

The database is automatically initialized on first use. The database file is stored at:
```
frontend/data/jobs.db
```

### Basic Operations

```python
from frontend.database import get_job_db, JobStatus

# Get database instance
job_db = get_job_db()

# Create a job
job = await job_db.create_job(
    request_body={'inputs': {...}, 'parameters': {...}},
    task_schema={'inputs': [...], 'parameters': [...]},
    endpoint='audio/transcribe'  # For chatbot jobs
    # OR
    # model_uid='model_123',
    # task_uid='task_456'  # For traditional jobs
)

# Update job status
await job_db.update_job_status(
    job['uid'],
    JobStatus.COMPLETED,
    response_body={'root': {...}}
)

# Get all jobs
jobs = await job_db.get_all_jobs()

# Get job by UID
job = await job_db.get_job_by_uid(job_uid)

# Delete job
await job_db.delete_job(job_uid)
```

## Integration

### Chatbot Integration

Jobs submitted through the chatbot interface are automatically saved to the database:

1. When a form is submitted via `chatbot_handlers.handle_form_submit()`, a job record is created
2. The job status is updated to `Completed` when the API call succeeds
3. The job status is updated to `Failed` if the API call fails

### Jobs Page Integration

The jobs listing page (`frontend/pages/jobs.py`) now loads jobs from the local database instead of the API, providing:
- Faster loading times
- Offline access to job history
- Local job management (cancel, delete)

### Job Details Page Integration

The job details page (`frontend/pages/job_details.py`) loads job information from the database and displays:
- Job metadata (UID, timestamps, status)
- Request inputs and parameters
- Response results

## Job Status Enum

```python
class JobStatus(str, Enum):
    RUNNING = 'Running'
    COMPLETED = 'Completed'
    FAILED = 'Failed'
    CANCELED = 'Canceled'
```

## File Structure

```
frontend/database/
├── __init__.py          # Package exports
├── job_db.py            # JobDB class and database operations
└── README.md            # This file

frontend/data/
└── jobs.db              # SQLite database file (auto-created)
```

## Notes

- The database uses lazy initialization - it's created on first access
- SQLite operations are synchronous, so the database can be used without async concerns for basic operations
- JSON fields (request, response, taskSchema) are automatically serialized/deserialized
- The database schema is automatically created if it doesn't exist
- Jobs are sorted by start time (newest first) by default

