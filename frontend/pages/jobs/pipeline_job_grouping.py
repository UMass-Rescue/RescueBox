"""
Group jobs for the /jobs list: multi-step pipelines share ``pipelineRootJobId``.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


def partition_jobs_by_pipeline(jobs: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """
    Split flat job rows into display groups.

    - Jobs with the same ``pipelineRootJobId`` (and the root row ``uid == root``) form one group.
    - Standalone jobs each get their own single-item group.

    Groups are sorted by newest activity first (max ``startTime`` in the group).
    Jobs inside a pipeline group are sorted oldest-first (run order).
    """
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

    def group_newest(members: List[Dict[str, Any]]) -> str:
        return max((x.get("startTime") or "" for x in members), default="")

    groups.sort(key=group_newest, reverse=True)
    return groups


def pipeline_group_root_id(group: List[Dict[str, Any]]) -> str:
    """Shared root job id for a non-empty pipeline group."""
    if not group:
        return ""
    return group[0].get("pipelineRootJobId") or group[0].get("uid") or ""
