"""
Log File Reader

This module provides functionality to read and filter log files based on
contextual IDs (job_id, model_id, session_id).

Usage:
    from frontend.utils.log_reader import read_logs_filtered
    
    # Read logs for a specific job
    logs = await read_logs_filtered(job_id='job_123')
    
    # Read logs matching multiple IDs
    logs = await read_logs_filtered(job_id='job_123', model_id='model_456')
"""

import logging
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from frontend.config import LOG_FILE

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Default log file path
DEFAULT_LOG_FILE = LOG_FILE


def parse_log_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a log line and extract timestamp, level, IDs, and message.
    
    Expected format:
        timestamp | level | job_id=xxx | model_id=yyy | session_id=zzz | logger | message
    
    Args:
        line: Log line to parse
    
    Returns:
        Dict with parsed log entry or None if parsing fails
    
    Tips:
    - Handles lines with or without context IDs
    - Extracts job_id, model_id, session_id from log format
    - Returns structured dict for easy filtering
    """
    if not line.strip():
        return None
    
    try:
        # Regex pattern to match log format
        # Format: timestamp | level | job_id=xxx | model_id=yyy | session_id=zzz | logger | message
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s*\| (.*?) \| (\S+) \| (.+)'
        match = re.match(pattern, line)
        
        if not match:
            # Try to parse as simple line (fallback)
            return {
                'timestamp': None,
                'level': 'UNKNOWN',
                'job_id': None,
                'model_id': None,
                'session_id': None,
                'logger': 'unknown',
                'message': line.strip(),
                'raw': line.strip()
            }
        
        # Handle both formats (with and without logger name)
        groups = match.groups()
        if len(groups) == 4:
            # Format without logger: timestamp | level | context | message
            timestamp_str, level, context_str, message = groups
            logger_name = 'unknown'
        else:
            # Format with logger: timestamp | level | context | logger | message
            timestamp_str, level, context_str, logger_name, message = groups
        
        # Parse timestamp
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            timestamp = None
        
        # Parse context IDs from context string
        job_id = None
        model_id = None
        session_id = None
        
        # Extract job_id=xxx, model_id=yyy, session_id=zzz
        job_match = re.search(r'job_id=([^\s|]+)', context_str)
        if job_match:
            job_id = job_match.group(1)
            if job_id == '-':
                job_id = None
        
        model_match = re.search(r'model_id=([^\s|]+)', context_str)
        if model_match:
            model_id = model_match.group(1)
            if model_id == '-':
                model_id = None
        
        session_match = re.search(r'session_id=([^\s|]+)', context_str)
        if session_match:
            session_id = session_match.group(1)
            if session_id == '-':
                session_id = None
        
        return {
            'timestamp': timestamp,
            'level': level,
            'job_id': job_id,
            'model_id': model_id,
            'session_id': session_id,
            'logger': logger_name,
            'message': message,
            'raw': line.strip()
        }
    except Exception as e:
        logger.debug("Failed to parse log line: %s, error: %s", line[:100], e)
        return None


async def read_logs_filtered(
    log_file_path: Optional[Path] = None,
    job_id: Optional[str] = None,
    model_id: Optional[str] = None,
    session_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Read log file and filter entries by contextual IDs and time range.
    
    Args:
        log_file_path: Path to log file (defaults to DATA_DIR/rescuebox.log)
        job_id: Filter by job ID (must match exactly)
        model_id: Filter by model ID (must match exactly)
        session_id: Filter by session ID (must match exactly)
        start_time: Filter entries after this time (inclusive)
        end_time: Filter entries before this time (inclusive)
    
    Returns:
        List of parsed log entries (dicts) matching the filters
    
    Tips:
    - All provided filters are applied with AND logic
    - If no filters provided, returns all log entries
    - Log entries are returned in chronological order
    - Handles missing log file gracefully (returns empty list)
    """
    if log_file_path is None:
        log_file_path = DEFAULT_LOG_FILE
    
    if not log_file_path.exists():
        logger.debug("Log file does not exist: %s", log_file_path)
        return []
    
    try:
        logger.debug("Reading logs from: %s", log_file_path)
        
        # Read all lines from log file
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Parse all log lines
        parsed_logs = []
        for line in lines:
            parsed = parse_log_line(line)
            if parsed:
                parsed_logs.append(parsed)
        
        # Filter by IDs
        filtered_logs = []
        for log_entry in parsed_logs:
            # Apply filters
            if job_id is not None and log_entry.get('job_id') != job_id:
                continue
            if model_id is not None and log_entry.get('model_id') != model_id:
                continue
            if session_id is not None and log_entry.get('session_id') != session_id:
                continue
            
            # Filter by time range
            entry_time = log_entry.get('timestamp')
            if entry_time:
                if start_time is not None and entry_time < start_time:
                    continue
                if end_time is not None and entry_time > end_time:
                    continue
            
            filtered_logs.append(log_entry)
        
        logger.info("Filtered %d log entries from %d total entries", len(filtered_logs), len(parsed_logs))
        return filtered_logs
    
    except Exception as e:
        logger.error("Error reading log file %s: %s", log_file_path, e, exc_info=True)
        return []


def get_log_file_path() -> Path:
    """
    Get the default log file path.
    
    Returns:
        Path: Path to default log file
    """
    return DEFAULT_LOG_FILE

