import logging
from typing import Optional, Dict, Any, List
from collections import defaultdict
from frontend.database import JobRecord
from frontend.api_client import APIClient

logger = logging.getLogger(__name__)

def extract_job_fields(job) -> Dict[str, Any]:
    """Extract job fields with backward compatibility for JobRecord and dict."""
    if isinstance(job, JobRecord):
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
            'pipelineMetadataFilterCriteria': getattr(job, 'pipelineMetadataFilterCriteria', None),
            'startTime': job.startTime,
            'endTime': job.endTime,
            'status': job.status.value if hasattr(job.status, 'value') else str(job.status),
            'statusText': job.statusText,
            'request': request,
            'response': response,
            'taskSchema': task_schema,
            'caseNotes': getattr(job, 'caseNotes', None),
        }
    return job if isinstance(job, dict) else {}

async def get_plugin_name(api_client: APIClient, model_uid: Optional[str]) -> Optional[str]:
    """Get model name by model UID."""
    if not model_uid:
        return None
    try:
        response = await api_client.get(f'/models/{model_uid}')
        if response.status_code == 200:
            return response.json().get('name')
    except Exception as e:
        logger.warning("Error fetching model name for %s: %s", model_uid, str(e))
    return None

def partition_jobs_by_pipeline(jobs: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Split flat job rows into display groups."""
    if not jobs:
        return []
    referred_roots = {j.get("pipelineRootJobId") for j in jobs if j.get("pipelineRootJobId")}

    def bucket_key(j: Dict[str, Any]) -> str:
        pr = j.get("pipelineRootJobId")
        if pr:
            return str(pr)
        uid = j.get("uid") or ""
        if uid in referred_roots:
            return uid
        return f"__single:{uid}"

    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for j in jobs:
        buckets[bucket_key(j)].append(j)

    groups: List[List[Dict[str, Any]]] = []
    for members in buckets.values():
        members_sorted = sorted(members, key=lambda x: x.get("startTime") or "")
        groups.append(members_sorted)

    groups.sort(key=lambda m: max((x.get("startTime") or "" for x in m), default=""), reverse=True)
    return groups

def pipeline_group_root_id(group: List[Dict[str, Any]]) -> str:
    if not group:
        return ""
    return group[0].get("pipelineRootJobId") or group[0].get("uid") or ""

def compute_job_results_title(endpoint_name: Optional[str], endpoint_name_chain: Optional[List[str]]) -> str:
    chain = endpoint_name_chain if isinstance(endpoint_name_chain, list) and endpoint_name_chain else None
    if not chain and endpoint_name:
        chain = [endpoint_name]
    if chain and len(chain) > 1:
        return "Results for: " + " → ".join(chain)
    if chain:
        return "Results for " + chain[0]
    return endpoint_name or "Results"
