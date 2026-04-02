"""
Build JSON-LD @graph from a normalized job dict using the CASE-UCO Python SDK.

See: https://github.com/vulnmaster/CASE-UCO-SDK — ``CASEGraph``, typed UCO/CASE classes,
``graph.validate()`` when ``case-utils`` / ``case_validate`` is installed.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

from case_uco import CASEGraph
from case_uco.case.investigation import InvestigativeAction, ProvenanceRecord
from case_uco.uco.analysis import ArtifactClassification, ArtifactClassificationResultFacet
from case_uco.uco.core import Assertion
from case_uco.uco.observable import Directory, File, FileFacet
from case_uco.uco.tool import AnalyticTool, Tool

KB_PREFIX = "http://rescuebox.org/kb/"
RB_NS = "http://rescuebox.org/ns/"  # @context prefix for rb: properties on export nodes


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
    return paths


def _extract_input_dir_paths(request: Any) -> List[str]:
    out: List[str] = []
    if not request or not isinstance(request, dict):
        return out
    ins = request.get("inputs") or {}
    if not isinstance(ins, dict):
        return out
    for v in ins.values():
        if isinstance(v, dict) and v.get("path"):
            p = str(v.get("path"))
            if p and os.path.isdir(p):
                out.append(p)
    return out


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


def _kb_id(path: str, prefix: str) -> str:
    import hashlib

    h = hashlib.sha256(path.encode("utf-8")).hexdigest()[:16]
    return f"kb:{prefix}-{h}"


def _endpoint_slug(endpoint: str) -> str:
    s = (endpoint or "unknown").replace("/", "_").replace(" ", "_")
    return s[:120] if len(s) > 120 else s


def _ordered_pipeline_endpoints(endpoint: str, chain: Any) -> List[str]:
    """
    Ordered list of RescueBox plugin endpoints for this job (pipeline + final).
    Used to emit one ``uco-tool:AnalyticTool`` per step on ``uco-action:instrument``.
    """
    out: List[str] = []
    if isinstance(chain, list):
        for x in chain:
            s = str(x).strip() if x is not None else ""
            if s and s not in out:
                out.append(s)
    ep = str(endpoint or "").strip()
    if ep and ep not in out:
        out.append(ep)
    if not out and ep:
        out = [ep]
    return out if out else ["unknown"]


def _map_action_status(status: str) -> str:
    s = (status or "").strip().lower()
    if s in ("completed", "success", "succeeded"):
        return "Success"
    if s in ("failed", "error"):
        return "Fail"
    if s in ("running", "pending", "queued"):
        return "Ongoing"
    return "Unknown"


def _parse_datetime(s: Any) -> datetime | None:
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _file_facet(path: str, *, is_dir: bool) -> FileFacet:
    p = Path(path)
    name = p.name or path
    ext = p.suffix.lstrip(".") if p.suffix else None
    facet = FileFacet(
        file_path=[str(path)],
        file_name=[name],
        is_directory=[is_dir],
    )
    if ext:
        facet.extension = ext
    return facet


def build_case_fragment_from_job_dict(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return JSON-LD with @context and @graph for one RescueBox job using ``CASEGraph``.

    Adds ``rb:requestSummary``, ``rb:outputSummary``, and ``rb:artifactPaths`` on the
    ``InvestigativeAction`` node for app compatibility.
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

    action_status = _map_action_status(status)
    req_summary = _summarize_request(request)
    out_summary = _output_summary(response)
    output_paths = _extract_output_paths(response)
    input_dir_paths = _extract_input_dir_paths(request)

    slug = _endpoint_slug(str(endpoint))
    inv_id = f"kb:inv-{uid}"
    result_id = f"kb:result-{uid}"
    prov_id = f"kb:provenance-{uid}"

    graph = CASEGraph(
        kb_prefix=KB_PREFIX,
        extra_context={
            "rb": RB_NS,
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        },
    )

    tool_rb = graph.create(
        Tool,
        id="kb:tool-rescuebox",
        name="RescueBox",
        version="3.0.0",
    )
    # One UCO AnalyticTool per pipeline step — each is an action:instrument (UCO action:instrument).
    pipeline_eps = _ordered_pipeline_endpoints(str(endpoint), chain)
    instruments: List[Any] = []
    for ep_step in pipeline_eps:
        slug_step = _endpoint_slug(ep_step)
        instruments.append(
            graph.create(
                AnalyticTool,
                id=f"kb:instrument-{slug_step}",
                name=ep_step,
                tool_type="RescueBox plugin endpoint",
            )
        )

    ac = graph.create(
        ArtifactClassification,
        id=f"kb:artifact-class-{uid}",
        class_=[str(endpoint or "unknown")],
    )
    acrf = graph.create(
        ArtifactClassificationResultFacet,
        id=f"kb:acrf-{uid}",
        classification=[ac],
    )

    summary_text = json.dumps(
        {
            "endpoint": endpoint,
            "endpointChain": chain,
            "status": status,
            "output": out_summary,
        },
        ensure_ascii=False,
    )[:8000]
    result_assertion = graph.create(
        Assertion,
        id=result_id,
        name=f"RescueBox job result {uid}",
        description=[summary_text],
        has_facet=[acrf],
    )

    st = _parse_datetime(str(start) if start else "")
    et = _parse_datetime(str(end) if end else "")

    inv_action = graph.create(
        InvestigativeAction,
        id=inv_id,
        name=f"RescueBox job: {endpoint or 'unknown'}",
        description=[
            json.dumps(
                {"endpoint": endpoint, "endpointChain": chain, "status": status},
                ensure_ascii=False,
            )
        ],
        performer=tool_rb,
        instrument=instruments,
        result=[result_assertion],
        action_status=[action_status],
        start_time=st,
        end_time=et,
    )

    dir_paths: Set[str] = set(input_dir_paths)
    for op in output_paths:
        try:
            parent = str(Path(op).parent)
            if parent and parent != op:
                dir_paths.add(parent)
        except Exception:
            pass

    observables: List[Any] = []
    for p in output_paths:
        ff = _file_facet(p, is_dir=False)
        observables.append(graph.create(File, id=_kb_id(p, "file"), has_facet=[ff]))

    for d in sorted(dir_paths):
        ff = _file_facet(d, is_dir=True)
        observables.append(graph.create(Directory, id=_kb_id(d, "dir"), has_facet=[ff]))

    # Provenance bundle: action, result, classification, platform tool, each instrument, observables
    prov_objects: List[Any] = [inv_action, result_assertion, ac, tool_rb]
    prov_objects.extend(instruments)
    prov_objects.extend(observables)

    graph.create(
        ProvenanceRecord,
        id=prov_id,
        exhibit_number=f"RB-JOB-{uid}",
        description=["Provenance bundle linking RescueBox investigative action to observables."],
        object=prov_objects,
    )

    doc = json.loads(graph.serialize())
    # Attach RescueBox extension properties for existing consumers (prefix from @context)
    for node in doc.get("@graph", []):
        if node.get("@id") == inv_id:
            node["rb:requestSummary"] = req_summary
            node["rb:outputSummary"] = out_summary
            node["rb:artifactPaths"] = output_paths
            break

    return doc


def build_jsonld_text(job: Dict[str, Any]) -> str:
    doc = build_case_fragment_from_job_dict(job)
    doc = _json_safe(doc)
    return json.dumps(doc, indent=2, ensure_ascii=False)
