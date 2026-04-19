"""
Job Utilities

Shared utility functions for job-related operations, including field extraction
and model name fetching.
"""

import logging
import httpx
from typing import Optional, Dict, Any, Tuple, List
from frontend.database import JobRecord
from frontend.api_client import APIClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def compute_job_results_title(
    endpoint: Optional[str],
    endpoint_chain: Optional[List[str]],
) -> str:
    """
    Build the job results card heading for single-endpoint vs multi-step pipelines.

    When ``endpoint_chain`` is set (ordered steps), the title lists the full chain.
    Otherwise falls back to ``endpoint`` alone.
    """
    chain = endpoint_chain if isinstance(endpoint_chain, list) and endpoint_chain else None
    if not chain and endpoint:
        chain = [endpoint]
    if chain and len(chain) > 1:
        return "Results for: " + " → ".join(chain)
    if chain:
        return "Results for " + chain[0]
    if endpoint:
        return "Results for " + endpoint
    return "Results"


def extract_job_fields(job) -> Dict[str, Any]:
    """
    Extract job fields with backward compatibility for JobRecord and dict.
    
    Normalizes job data access to work with both Pydantic JobRecord models
    and legacy dictionary format.
    
    Args:
        job: JobRecord Pydantic model or dict
    
    Returns:
        Dict[str, Any]: Dictionary with normalized job fields:
            - uid (str)
            - modelUid (Optional[str])
            - taskUid (Optional[str])
            - endpoint (Optional[str])
            - endpointChain (Optional[list[str]]): ordered endpoints for multi-step chatbot jobs
            - pipelineRootJobId (Optional[str]): first job id for a multi-step pipeline run
            - startTime (Optional[str])
            - endTime (Optional[str])
            - status (str)
            - statusText (Optional[str])
            - request (Union[RequestBody, Dict])
            - response (Optional[Union[ResponseBody, Dict]])
            - taskSchema (Union[TaskSchema, Dict])
    
    Tips:
    - Handles both JobRecord (Pydantic model) and dict formats
    - Converts Pydantic models to dicts using model_dump()
    - Status enum values are converted to strings
    """
    if isinstance(job, JobRecord):
        # Extract from Pydantic model
        request = job.request.model_dump() if hasattr(job.request, 'model_dump') else job.request
        task_schema = job.taskSchema.model_dump() if hasattr(job.taskSchema, 'model_dump') else job.taskSchema
        response = job.response.model_dump() if job.response and hasattr(job.response, 'model_dump') else job.response
        
        return {
            'uid': job.uid,
            'modelUid': job.modelUid,
            'taskUid': job.taskUid,
            'endpoint': job.endpoint,
            'endpointChain': getattr(job, 'endpointChain', None),
            'pipelineRootJobId': getattr(job, 'pipelineRootJobId', None),
            'pipelineMetadataFilterCriteria': getattr(
                job, 'pipelineMetadataFilterCriteria', None
            ),
            'startTime': job.startTime,
            'endTime': job.endTime,
            'status': job.status.value if hasattr(job.status, 'value') else str(job.status),
            'statusText': job.statusText,
            'request': request,
            'response': response,
            'taskSchema': task_schema,
            'caseNotes': getattr(job, 'caseNotes', None),
        }
    else:
        # Legacy dict access
        return {
            'uid': job.get('uid', 'Unknown'),
            'modelUid': job.get('modelUid'),
            'taskUid': job.get('taskUid'),
            'endpoint': job.get('endpoint'),
            'endpointChain': job.get('endpointChain'),
            'pipelineRootJobId': job.get('pipelineRootJobId'),
            'pipelineMetadataFilterCriteria': job.get('pipelineMetadataFilterCriteria'),
            'startTime': job.get('startTime'),
            'endTime': job.get('endTime'),
            'status': job.get('status', 'Unknown'),
            'statusText': job.get('statusText'),
            'request': job.get('request', {}),
            'response': job.get('response'),
            'taskSchema': job.get('taskSchema', {}),
            'caseNotes': job.get('caseNotes'),
        }


async def get_plugin_name(api_client: APIClient, model_uid: Optional[str]) -> Optional[str]:
    """
    Get model name by model UID.
    
    Fetches model information from the API and extracts the name.
    
    Args:
        api_client: API client instance for API requests
        model_uid (Optional[str]): Model unique identifier
    
    Returns:
        Optional[str]: Model name if found, None otherwise
    
    Tips:
    - Returns None if model_uid is not provided
    - Errors are silently handled (returns None)
    - Used for displaying model names in job rows and details
    """
    if not model_uid:
        #logger.debug("No model_uid provided, returning None")
        return None
    try:
        #logger.debug("Fetching model name for UID: %s", model_uid)
        response = await api_client.get(f'/models/{model_uid}')
        if response.status_code == 200:
            plugin_name = response.json().get('name')
            #logger.debug("Model name fetched: %s", plugin_name)
            return plugin_name
    except Exception as e:
        logger.warning("Error fetching model name for %s: %s", model_uid, str(e))
        pass
    return None
