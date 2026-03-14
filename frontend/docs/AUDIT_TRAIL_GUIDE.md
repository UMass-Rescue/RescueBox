# Audit Trail Guide

## Overview

The RescueBox Desktop frontend includes a comprehensive audit trail feature that allows users to generate detailed reports of job executions. Audit trails capture all relevant information including user prompts, tool selections, inputs, parameters, outputs, errors, and application logs.

## Features

### What's Included in Audit Trails

Audit trails capture the following information for each job:

1. **Job Information**
   - Job ID
   - Status (Running, Completed, Failed, Canceled)
   - Start and end times
   - Model/endpoint information

2. **User Chat Prompts**
   - All user messages that led to job creation
   - Timestamps for each prompt
   - Related conversation context

3. **Tool Selection**
   - Selected tool/endpoint
   - Model UID (for traditional jobs)
   - Task UID (for traditional jobs)
   - Endpoint name (for chatbot jobs)

4. **Inputs and Parameters**
   - All input values (files, directories, text)
   - All parameter values (sliders, dropdowns, text)
   - Formatted for easy reading

5. **Outputs/Results**
   - Complete response data
   - Formatted as JSON for structured data
   - File paths and metadata

6. **Errors**
   - Error messages (if job failed)
   - Status text for canceled jobs

7. **Application Logs**
   - Filtered logs matching the job's IDs
   - Only includes logs from job execution window
   - Chronologically ordered

## Usage

### Exporting Audit Trail

1. Navigate to the **Jobs** page
2. Click on a job to view details
3. Click the **"📋 Export Audit Trail"** button
4. The audit trail will be downloaded as a Markdown file

### File Format

Audit trails are exported as Markdown (`.md`) files with the following naming convention:

```
audit_trail_job_{job_id}_{timestamp}.md
```

Example: `audit_trail_job_abc12345_20240115_143022.md`

### Export Format

The audit trail is structured as a Markdown document with the following sections:

```markdown
# RescueBox Audit Trail

**Generated:** 2024-01-15T14:30:22

## Job Information
- **Job ID:** `abc12345`
- **Status:** Completed
- **Start Time:** 2024-01-15T14:25:00
- **End Time:** 2024-01-15T14:28:30
- **Endpoint:** audio/transcribe

## User Prompts
### Prompt (2024-01-15T14:24:55)
Please transcribe this audio file

## Tool Selection
- **Tool:** `audio/transcribe`

## Inputs and Parameters
### Inputs
- **audio_file:** `/path/to/audio.wav` (file/directory)
### Parameters
- **language:** `en`

## Outputs
```json
{
  "text": "Transcribed text here..."
}
```

## Application Logs
The following log entries match this job:

```
2024-01-15 14:25:00 | INFO     | frontend.pages.chatbot.chatbot_handlers | Job abc12345 created in database
2024-01-15 14:25:05 | INFO     | frontend.chatbot.core | Submitting job to endpoint: audio/transcribe
2024-01-15 14:28:30 | INFO     | frontend.database.job_db | Job abc12345 updated to Completed status
```
```

## Implementation Details

### Audit Trail Generation

The audit trail generation is handled by `frontend/utils/audit_trail.py`:

```python
from frontend.utils.audit_trail import generate_audit_trail_for_job, export_audit_trail

# Generate audit trail for a job
audit_trail = await generate_audit_trail_for_job(job_id)

# Export as markdown
markdown_content = await export_audit_trail(audit_trail, format_type='markdown')
```

### Log Filtering

Application logs are filtered using contextual logging information:

- **Job ID**: Matches logs with the specific job_id
- **Model ID**: Matches logs with the specific model_uid
- **Time Range**: Only includes logs from job start to end time

See [Logging Context Guide](#logging-context) for details on how contextual logging works.

### Related Chat Messages

The audit trail includes related chat messages by:

1. Searching all conversations for messages with matching tool call endpoints
2. Matching messages that reference the same endpoint as the job
3. Including conversation context and timestamps

## Integration with Logging Context

Audit trails rely on the contextual logging system to filter logs. When jobs are created:

1. Logging context is set with `job_id`, `model_id`, and `session_id`
2. All subsequent log messages include these IDs
3. During audit trail generation, logs are filtered by these IDs

For more information, see `docs/LOGGING_GUIDE.md`.

## File Locations

- **Audit Trail Generator**: `frontend/utils/audit_trail.py`
- **UI Component**: `frontend/pages/jobs/job_audit.py`
- **Integration**: `frontend/pages/jobs/job_details.py`

## Future Enhancements

Potential improvements to the audit trail feature:

1. **Export Formats**: Support for JSON, CSV, PDF formats
2. **Bulk Export**: Export audit trails for multiple jobs
3. **Conversation Trails**: Generate audit trails for entire conversations
4. **Log Aggregation**: Include logs from related jobs
5. **Search Integration**: Search within audit trails
6. **Automatic Archiving**: Automatically archive audit trails

## Related Documentation

- [Logging Guide](LOGGING_GUIDE.md) - Contextual logging system
- [Job Database](database/README.md) - Job storage and retrieval
- [Chat History](CHAT_HISTORY_README.md) - Conversation management

