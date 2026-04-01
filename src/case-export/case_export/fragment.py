"""
Build a small JSON-LD @graph from a normalized job dict (uid, endpoint, times, request, response).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

# Namespace prefixes aligned with CASE/UCO public documentation (fragment-only; not SHACL-validated).
_CONTEXT: Dict[str, Any] = {
    "uco": "https://ontology.unifiedcyberontology.org/uco/",
    "case": "https://ontology.caseontology.org/case/case/",
    "kb": "http://rescuebox.org/kb/",
    "rb": "http://rescuebox.org/ns/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}


def _json_safe(obj: Any) -> Any:
    """Recursively convert Path / PathLike and other non-JSON values for json.dumps."""
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    try:
        if isinstance(obj, os.PathLike):
            return os.fspath(obj)
    except Exception:
        pass
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(x) for x in obj]
    return str(obj)


def _summarize_request(req: Any) -> Dict[str, Any]:
    if not req:
        return {}
    if isinstance(req, dict):
        out: Dict[str, Any] = {}
        ins = req.get("inputs") or {}
        params = req.get("parameters") or {}
        if isinstance(ins, dict):
            for k, v in list(ins.items())[:24]:
                if isinstance(v, dict) and "path" in v:
                    out[f"input:{k}"] = v.get("path")
                elif isinstance(v, dict) and "text" in v:
                    t = v.get("text")
                    out[f"input:{k}"] = (t[:200] + "…") if isinstance(t, str) and len(t) > 200 else t
                else:
                    out[f"input:{k}"] = str(v)[:300]
        if isinstance(params, dict):
            for k, v in list(params.items())[:32]:
                out[f"param:{k}"] = _json_safe(v)
        return out
    return {"repr": str(req)[:500]}


def _extract_output_paths(response: Any) -> List[str]:
    paths: List[str] = []
    if not response:
        return paths
    if isinstance(response, dict):
        root = response.get("root") or response
        if not isinstance(root, dict):
            return paths
        ot = root.get("output_type")
        if ot == "batchfile":
            for f in root.get("files") or []:
                if isinstance(f, dict) and f.get("path"):
                    paths.append(str(f["path"]))
        elif ot == "file" and root.get("path"):
            paths.append(str(root["path"]))
        elif ot == "text" and root.get("value"):
            # keep snippet only in summary, not as path
            pass
    return paths


def _output_summary(response: Any) -> Dict[str, Any]:
    if not response:
        return {}
    if isinstance(response, dict):
        root = response.get("root") or response
        if not isinstance(root, dict):
            return {"raw": json.dumps(response, default=str)[:2000]}
        ot = root.get("output_type")
        summary: Dict[str, Any] = {"output_type": ot}
        paths = _extract_output_paths(response)
        if paths:
            summary["artifact_paths"] = paths[:500]
            summary["artifact_count"] = len(paths)
        if ot == "text" and isinstance(root.get("value"), str):
            v = root["value"]
            summary["text_preview"] = v[:1500] + ("…" if len(v) > 1500 else "")
        return summary
    return {"repr": str(response)[:1500]}


def build_case_fragment_from_job_dict(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a JSON-LD document with @context and @graph describing one RescueBox job run.

    Uses uco:Action for the forensic processing step and uco:CyberObservable (simplified
    as bare file path references) for batch outputs when paths are known.
    """
    uid = str(job.get("uid") or "unknown")
    endpoint = job.get("endpoint") or ""
    chain = job.get("endpointChain")
    status = str(job.get("status") or "")
    start = job.get("startTime") or ""
    end = job.get("endTime") or ""

    request = job.get("request")
    if hasattr(request, "model_dump"):
        try:
            request = request.model_dump(mode="json")
        except Exception:
            request = request.model_dump()
    if isinstance(request, dict):
        request = _json_safe(request)

    response = job.get("response")
    if hasattr(response, "model_dump"):
        try:
            response = response.model_dump(mode="json")
        except Exception:
            response = response.model_dump()
    if isinstance(response, dict):
        response = _json_safe(response)

    action_id = f"kb:rescuebox-job-{uid}"
    tool_id = "kb:tool-rescuebox"

    graph: List[Dict[str, Any]] = [
        {
            "@id": tool_id,
            "@type": "uco:Tool",
            "uco:name": "RescueBox",
            "uco:version": "3.0.0",
        },
        {
            "@id": action_id,
            "@type": "uco:Action",
            "uco:name": f"Plugin run: {endpoint or 'unknown'}",
            "uco:description": json.dumps(
                {
                    "endpoint": endpoint,
                    "endpointChain": chain,
                    "status": status,
                    "startTime": start,
                    "endTime": end,
                },
                ensure_ascii=False,
            ),
            "uco:performer": {"@id": tool_id},
            "rb:requestSummary": _summarize_request(request),
            "rb:outputSummary": _output_summary(response),
            "rb:artifactPaths": _extract_output_paths(response),
        },
    ]

    return {"@context": _CONTEXT, "@graph": graph}


def build_jsonld_text(job: Dict[str, Any]) -> str:
    doc = build_case_fragment_from_job_dict(job)
    doc = _json_safe(doc)
    return json.dumps(doc, indent=2, ensure_ascii=False)
