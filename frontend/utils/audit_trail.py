"""
Audit Trail Generator

This module provides functionality to generate comprehensive audit trails
that include user chat prompts, tool selections, inputs/parameters, outputs,
errors, and logs. The audit trail can be exported to a file.

Usage:
    from frontend.utils.audit_trail import generate_audit_trail_for_job, export_audit_trail
    
    # Generate audit trail for a job
    trail = await generate_audit_trail_for_job(job_id)
    
    # Export to file
    await export_audit_trail(trail, 'audit_trail.md')
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from frontend.database import get_job_db, get_chat_history_db
from frontend.utils.log_reader import read_logs_filtered, get_log_file_path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def generate_audit_trail_for_job(job_id: str) -> Dict[str, Any]:
    """
    Generate audit trail for a specific job.
    
    Collects all relevant information including:
    - Job metadata (timestamps, status)
    - Tool/endpoint information
    - Inputs and parameters
    - Outputs/results
    - Errors (if any)
    - Related chat messages (if job was created via chatbot)
    
    Args:
        job_id (str): Job unique identifier
    
    Returns:
        Dict[str, Any]: Audit trail data dictionary
    
    Tips:
    - Includes all job details from database
    - Links to related chat messages if available
    - Formats data for easy export
    """
    logger.info("Generating audit trail for job: %s", job_id)
    
    job_db = get_job_db()
    job = await job_db.get_job_by_uid(job_id)
    
    if not job:
        logger.error("Job %s not found", job_id)
        return {'error': f'Job {job_id} not found'}
    
    # Extract job data - handle Pydantic models
    if hasattr(job, 'model_dump'):
        job_dict = job.model_dump()
        # Convert nested Pydantic models to dicts if needed
        if hasattr(job_dict.get('request'), 'model_dump'):
            job_dict['request'] = job_dict['request'].model_dump()
        if hasattr(job_dict.get('response'), 'model_dump'):
            job_dict['response'] = job_dict['response'].model_dump()
        if hasattr(job_dict.get('taskSchema'), 'model_dump'):
            job_dict['taskSchema'] = job_dict['taskSchema'].model_dump()
    else:
        job_dict = job
    
    # Find related chat messages
    related_messages = []
    try:
        chat_history_db = get_chat_history_db()
        # Search for messages that reference this job
        # (This is a simplified search - in production, you might store job_id in message metadata)
        all_conversations = await chat_history_db.get_all_conversations()
        for conv in all_conversations:
            messages = await chat_history_db.get_messages(conv.conversation_id)
            for msg in messages:
                if msg.tool_call_endpoint == job_dict.get('endpoint'):
                    # Check if arguments match (simplified matching)
                    related_messages.append({
                        'conversation_id': conv.conversation_id,
                        'message_id': msg.message_id,
                        'role': msg.role,
                        'content': msg.content,
                        'timestamp': msg.timestamp,
                        'tool_call_endpoint': msg.tool_call_endpoint,
                        'tool_call_arguments': msg.tool_call_arguments
                    })
    except Exception as e:
        logger.debug("Could not fetch related chat messages: %s", e)
    
    audit_trail = {
        'job_id': job_id,
        'generated_at': datetime.now().isoformat(),
        'job': {
            'uid': job_dict.get('uid'),
            'modelUid': job_dict.get('modelUid'),
            'taskUid': job_dict.get('taskUid'),
            'endpoint': job_dict.get('endpoint'),
            'startTime': job_dict.get('startTime'),
            'endTime': job_dict.get('endTime'),
            'status': job_dict.get('status'),
            'statusText': job_dict.get('statusText'),  # Errors
        },
        'tool': {
            'selected': job_dict.get('endpoint') or f"{job_dict.get('modelUid')}/{job_dict.get('taskUid')}",
        },
        'inputs': {},
        'parameters': {},
        'outputs': job_dict.get('response'),
        'errors': job_dict.get('statusText') if job_dict.get('status') in ['Failed', 'Canceled'] else None,
        'related_chat_messages': related_messages,
        'task_schema': job_dict.get('taskSchema')
    }
    
    # Extract inputs and parameters from request
    request_data = job_dict.get('request', {})
    if isinstance(request_data, dict):
        audit_trail['inputs'] = request_data.get('inputs', {})
        audit_trail['parameters'] = request_data.get('parameters', {})
    elif hasattr(request_data, 'model_dump'):
        request_dict = request_data.model_dump()
        audit_trail['inputs'] = request_dict.get('inputs', {})
        audit_trail['parameters'] = request_dict.get('parameters', {})
    
    # Read and filter logs for this job
    try:
        job_start_time = datetime.fromisoformat(job_dict.get('startTime', '')) if job_dict.get('startTime') else None
        job_end_time = datetime.fromisoformat(job_dict.get('endTime', '')) if job_dict.get('endTime') else None
        
        # Read logs matching this job ID and model ID
        job_logs = await read_logs_filtered(
            job_id=job_dict.get('uid'),
            model_id=job_dict.get('modelUid'),
            start_time=job_start_time,
            end_time=job_end_time
        )
        audit_trail['logs'] = job_logs
    except Exception as e:
        logger.debug("Could not read logs for job %s: %s", job_id, e)
        audit_trail['logs'] = []
    
    logger.info("Audit trail generated successfully for job: %s", job_id)
    return audit_trail


async def generate_audit_trail_for_conversation(conversation_id: str) -> Dict[str, Any]:
    """
    Generate audit trail for a conversation.
    
    Collects all relevant information including:
    - Conversation metadata
    - User prompts
    - Tool selections
    - Job information (for each tool call)
    - Outputs and errors
    
    Args:
        conversation_id (str): Conversation unique identifier
    
    Returns:
        Dict[str, Any]: Audit trail data dictionary
    """
    logger.info("Generating audit trail for conversation: %s", conversation_id)
    
    chat_history_db = get_chat_history_db()
    conversation = await chat_history_db.get_conversation(conversation_id)
    
    if not conversation:
        logger.error("Conversation %s not found", conversation_id)
        return {'error': f'Conversation {conversation_id} not found'}
    
    messages = await chat_history_db.get_messages(conversation_id)
    job_db = get_job_db()
    
    # Collect all jobs related to this conversation
    related_jobs = []
    for msg in messages:
        if msg.tool_call_endpoint:
            # Try to find related job by endpoint and arguments
            # This is a simplified search - in production, store job_id in message metadata
            all_jobs = await job_db.get_all_jobs()
            for job in all_jobs:
                job_dict = job.model_dump() if hasattr(job, 'model_dump') else job
                if job_dict.get('endpoint') == msg.tool_call_endpoint:
                    related_jobs.append({
                        'job_id': job_dict.get('uid'),
                        'job': job_dict
                    })
    
    audit_trail = {
        'conversation_id': conversation_id,
        'generated_at': datetime.now().isoformat(),
        'conversation': {
            'title': conversation.title,
            'created_at': conversation.created_at,
            'updated_at': conversation.updated_at,
            'message_count': conversation.message_count
        },
        'messages': [
            {
                'message_id': msg.message_id,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp,
                'tool_call_endpoint': msg.tool_call_endpoint,
                'tool_call_arguments': msg.tool_call_arguments,
                'message_type': msg.message_type
            }
            for msg in messages
        ],
        'related_jobs': related_jobs
    }
    
    logger.info("Audit trail generated successfully for conversation: %s", conversation_id)
    return audit_trail


def format_audit_trail_markdown(audit_trail: Dict[str, Any]) -> str:
    """
    Format audit trail as markdown document.
    
    Creates a human-readable markdown document from audit trail data.
    
    Args:
        audit_trail (Dict[str, Any]): Audit trail data dictionary
    
    Returns:
        str: Formatted markdown string
    
    Tips:
    - Includes all sections: prompts, tools, inputs, outputs, errors
    - Uses markdown formatting for readability
    - Handles missing data gracefully
    """
    logger.debug("Formatting audit trail as markdown")
    
    lines = []
    lines.append("# RescueBox Audit Trail")
    lines.append("")
    lines.append(f"**Generated:** {audit_trail.get('generated_at', datetime.now().isoformat())}")
    lines.append("")
    
    # Job information
    if 'job_id' in audit_trail:
        job_info = audit_trail.get('job', {})
        lines.append("## Job Information")
        lines.append("")
        lines.append(f"- **Job ID:** `{audit_trail['job_id']}`")
        lines.append(f"- **Status:** {job_info.get('status', 'Unknown')}")
        lines.append(f"- **Start Time:** {job_info.get('startTime', 'Unknown')}")
        lines.append(f"- **End Time:** {job_info.get('endTime', 'N/A')}")
        if job_info.get('modelUid'):
            lines.append(f"- **Model:** {job_info.get('modelUid')}")
        if job_info.get('endpoint'):
            lines.append(f"- **Endpoint:** {job_info.get('endpoint')}")
        lines.append("")
    
    # Conversation information
    if 'conversation_id' in audit_trail:
        conv_info = audit_trail.get('conversation', {})
        lines.append("## Conversation Information")
        lines.append("")
        lines.append(f"- **Conversation ID:** `{audit_trail['conversation_id']}`")
        lines.append(f"- **Title:** {conv_info.get('title', 'Untitled')}")
        lines.append(f"- **Created:** {conv_info.get('created_at', 'Unknown')}")
        lines.append(f"- **Messages:** {conv_info.get('message_count', 0)}")
        lines.append("")
    
    # User prompts
    if 'messages' in audit_trail:
        lines.append("## User Prompts")
        lines.append("")
        for msg in audit_trail['messages']:
            if msg['role'] == 'user':
                lines.append(f"### Prompt ({msg.get('timestamp', 'Unknown time')})")
                lines.append("")
                lines.append(msg.get('content', ''))
                lines.append("")
    
    # Related chat messages
    if 'related_chat_messages' in audit_trail and audit_trail['related_chat_messages']:
        lines.append("## Related Chat Messages")
        lines.append("")
        for msg in audit_trail['related_chat_messages']:
            lines.append(f"### {msg.get('role', 'unknown').title()} Message ({msg.get('timestamp', 'Unknown')})")
            lines.append("")
            lines.append(msg.get('content', ''))
            lines.append("")
    
    # Tool selection
    if 'tool' in audit_trail:
        tool_info = audit_trail['tool']
        lines.append("## Tool Selection")
        lines.append("")
        lines.append(f"- **Tool:** `{tool_info.get('selected', 'Unknown')}`")
        lines.append("")
    
    # Inputs and Parameters
    if audit_trail.get('inputs') or audit_trail.get('parameters'):
        lines.append("## Inputs and Parameters")
        lines.append("")
        
        if audit_trail.get('inputs'):
            lines.append("### Inputs")
            lines.append("")
            for key, value in audit_trail['inputs'].items():
                if isinstance(value, dict):
                    # Handle Input union types
                    if 'path' in value:
                        lines.append(f"- **{key}:** `{value['path']}` (file/directory)")
                    elif 'text' in value:
                        text_preview = value['text'][:200] + '...' if len(value['text']) > 200 else value['text']
                        lines.append(f"- **{key}:** {text_preview}")
                    else:
                        lines.append(f"- **{key}:** `{json.dumps(value, indent=2)}`")
                else:
                    lines.append(f"- **{key}:** `{value}`")
            lines.append("")
        
        if audit_trail.get('parameters'):
            lines.append("### Parameters")
            lines.append("")
            for key, value in audit_trail['parameters'].items():
                lines.append(f"- **{key}:** `{value}`")
            lines.append("")
    
    # Outputs
    if 'outputs' in audit_trail and audit_trail['outputs']:
        lines.append("## Outputs")
        lines.append("")
        outputs = audit_trail['outputs']
        if isinstance(outputs, dict):
            lines.append("```json")
            lines.append(json.dumps(outputs, indent=2))
            lines.append("```")
        else:
            lines.append(str(outputs))
        lines.append("")
    
    # Errors
    if 'errors' in audit_trail and audit_trail['errors']:
        lines.append("## Errors")
        lines.append("")
        lines.append(f"```")
        lines.append(audit_trail['errors'])
        lines.append("```")
        lines.append("")
    
    # Related jobs
    if 'related_jobs' in audit_trail and audit_trail['related_jobs']:
        lines.append("## Related Jobs")
        lines.append("")
        for job_item in audit_trail['related_jobs']:
            job_data = job_item.get('job', {})
            lines.append(f"### Job {job_item.get('job_id', 'Unknown')}")
            lines.append("")
            lines.append(f"- **Status:** {job_data.get('status', 'Unknown')}")
            lines.append(f"- **Start Time:** {job_data.get('startTime', 'Unknown')}")
            lines.append("")
    
    # Application Logs
    if 'logs' in audit_trail and audit_trail['logs']:
        lines.append("## Application Logs")
        lines.append("")
        lines.append("The following log entries match this job:")
        lines.append("")
        lines.append("```")
        for log_entry in audit_trail['logs']:
            timestamp_str = log_entry.get('timestamp').strftime('%Y-%m-%d %H:%M:%S') if log_entry.get('timestamp') else 'N/A'
            level = log_entry.get('level', 'UNKNOWN')
            logger_name = log_entry.get('logger', 'unknown')
            message = log_entry.get('message', '')
            lines.append(f"{timestamp_str} | {level:8s} | {logger_name} | {message}")
        lines.append("```")
        lines.append("")
    
    return "\n".join(lines)


async def export_audit_trail(audit_trail: Dict[str, Any], format_type: str = 'markdown') -> str:
    """
    Export audit trail to a formatted string.
    
    Args:
        audit_trail (Dict[str, Any]): Audit trail data dictionary
        format_type (str): Export format ('markdown', 'json'). Defaults to 'markdown'
    
    Returns:
        str: Formatted audit trail string ready for file export
    
    Tips:
    - Markdown format is human-readable
    - JSON format is machine-readable
    - Use format_audit_trail_markdown() for markdown formatting
    """
    logger.info("Exporting audit trail in format: %s", format_type)
    
    if format_type == 'markdown':
        return format_audit_trail_markdown(audit_trail)
    elif format_type == 'json':
        return json.dumps(audit_trail, indent=2, default=str)
    else:
        raise ValueError(f"Unsupported format type: {format_type}")



