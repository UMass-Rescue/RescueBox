"""
Build JSON-LD @graph from a normalized job dict using the CASE-UCO Python SDK.

See: https://github.com/vulnmaster/CASE-UCO-SDK — ``CASEGraph``, typed UCO/CASE classes,
``graph.validate()`` when ``case-utils`` / ``case_validate`` is installed.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from case_uco import CASEGraph
from case_uco.case.investigation import InvestigativeAction, ProvenanceRecord
from case_uco.uco.core import Assertion, Relationship
from case_uco.uco.observable import (
    ContentData,
    ContentDataFacet,
    Directory,
    File,
    FileFacet,
    RasterPicture,
    RasterPictureFacet,
)
from case_uco.uco.tool import AnalyticTool, Tool
from case_uco.uco.types import Hash

KB_PREFIX = "http://rescuebox.org/kb/"
RB_NS = "http://rescuebox.org/ns/"  # @context prefix for rb: properties on export nodes

_RASTER_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}


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
    """Legacy compact summary for consumers that still read rb:requestSummary."""
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
                    out[f"input:{k}"] = (
                        (t[:200] + "…") if isinstance(t, str) and len(t) > 200 else t
                    )
                else:
                    out[f"input:{k}"] = str(v)[:300]
        if isinstance(params, dict):
            for k, v in list(params.items())[:32]:
                out[f"param:{k}"] = _json_safe(v)
        return out
    return {"repr": str(req)[:500]}


def _parse_request_structure(
    request: Any,
) -> Tuple[List[str], List[Tuple[str, str]], Dict[str, Any]]:
    """
    Return (directory_paths, (input_key, full_text) pairs, flat parameters dict).
    Text inputs are not truncated.
    """
    dirs: List[str] = []
    texts: List[Tuple[str, str]] = []
    params_flat: Dict[str, Any] = {}
    if not request or not isinstance(request, dict):
        return dirs, texts, params_flat
    ins = request.get("inputs") or {}
    if isinstance(ins, dict):
        for key, v in ins.items():
            if isinstance(v, dict) and "path" in v:
                p = str(v.get("path") or "")
                if not p:
                    continue
                kl = key.lower()
                # Directory inputs are often named *input_dir* / *_dir; path may not exist in export env.
                dir_intent = kl.endswith("_dir") or kl in ("directory", "folder")
                if os.path.isdir(p) or dir_intent:
                    dirs.append(p)
                else:
                    texts.append((f"input:{key}:path_file", p))
            elif isinstance(v, dict) and "text" in v:
                t = v.get("text")
                if isinstance(t, str):
                    texts.append((f"input:{key}", t))
    params = request.get("parameters") or {}
    if isinstance(params, dict):
        for k, v in params.items():
            params_flat[str(k)] = _json_safe(v)
    return dirs, texts, params_flat


def _infer_output_type_from_root(root: Dict[str, Any]) -> Optional[str]:
    """
    Normalize ``output_type`` when the wire payload omits it but shape matches a known union.
    Keeps ``rb:outputType`` aligned with ``rb:outputSummary["output_type"]``.
    """
    ot = root.get("output_type")
    if isinstance(ot, str) and ot.strip():
        return ot.strip()
    files = root.get("files")
    if isinstance(files, list) and files:
        first = files[0]
        if isinstance(first, dict) and first.get("path"):
            return "batchfile"
    if root.get("path"):
        return "file"
    if isinstance(root.get("value"), str):
        return "text"
    return None


def _parse_batch_file_rows(response: Any) -> List[Dict[str, Any]]:
    """
    Rows from batchfile / BatchFileResponse: path, rank, similarity, model_name, metadata.
    """
    rows: List[Dict[str, Any]] = []
    if not response or not isinstance(response, dict):
        return rows
    root = response.get("root") or response
    if not isinstance(root, dict):
        return rows
    if _infer_output_type_from_root(root) != "batchfile":
        return rows
    files = root.get("files") or []
    for i, f in enumerate(files):
        if not isinstance(f, dict) or not f.get("path"):
            continue
        path = str(f["path"])
        meta = f.get("metadata") if isinstance(f.get("metadata"), dict) else {}
        sim: Optional[float] = None
        raw_sim = meta.get("Similarity")
        if raw_sim is not None:
            try:
                sim = float(raw_sim)
            except (TypeError, ValueError):
                pass
        model_name = meta.get("Model")
        if model_name is not None:
            model_name = str(model_name)
        rows.append(
            {
                "path": path,
                "rank": i + 1,
                "similarity": sim,
                "model_name": model_name,
                "metadata": dict(meta),
            }
        )
    return rows


def _extract_output_paths(response: Any) -> List[str]:
    rows = _parse_batch_file_rows(response)
    if rows:
        return [r["path"] for r in rows]
    paths: List[str] = []
    if not response:
        return paths
    if isinstance(response, dict):
        root = response.get("root") or response
        if not isinstance(root, dict):
            return paths
        ot = _infer_output_type_from_root(root)
        if ot == "batchfile":
            for f in root.get("files") or []:
                if isinstance(f, dict) and f.get("path"):
                    paths.append(str(f["path"]))
        elif ot == "file" and root.get("path"):
            paths.append(str(root["path"]))
    return paths


def _extract_input_dir_paths(request: Any) -> List[str]:
    dirs, _, _ = _parse_request_structure(request)
    return dirs


def _output_summary(response: Any) -> Dict[str, Any]:
    if not response:
        return {}
    if isinstance(response, dict):
        root = response.get("root") or response
        if not isinstance(root, dict):
            return {"raw": json.dumps(response, default=str)[:2000]}
        ot = _infer_output_type_from_root(root)
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


def _is_raster_path(path: str) -> bool:
    try:
        return Path(path).suffix.lower() in _RASTER_EXT
    except Exception:
        return False


def _local_file_forensics(path: str) -> Dict[str, Any]:
    """Best-effort size, mtimes, mime, sha256 when the path is a readable file."""
    out: Dict[str, Any] = {}
    try:
        st = os.stat(path)
        out["size_in_bytes"] = int(st.st_size)
        out["modified_time"] = datetime.fromtimestamp(st.st_mtime)
        out["accessed_time"] = datetime.fromtimestamp(st.st_atime)
    except OSError:
        return out
    mime_guess, _ = mimetypes.guess_type(path)
    if mime_guess:
        out["mime_type"] = mime_guess
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fp:
            for chunk in iter(lambda: fp.read(1024 * 1024), b""):
                h.update(chunk)
        out["sha256_hex"] = h.hexdigest()
    except OSError:
        pass
    return out


def _file_facet(
    path: str, *, is_dir: bool, forensics: Optional[Dict[str, Any]] = None
) -> FileFacet:
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
    if forensics:
        if forensics.get("size_in_bytes") is not None:
            facet.size_in_bytes = forensics["size_in_bytes"]
        if forensics.get("modified_time"):
            facet.modified_time = forensics["modified_time"]
        if forensics.get("accessed_time"):
            facet.accessed_time = forensics["accessed_time"]
    return facet


def _raster_facet(path: str) -> RasterPictureFacet:
    ext = Path(path).suffix.lower().lstrip(".")
    rf = RasterPictureFacet()
    if ext in ("jpg", "jpeg"):
        rf.picture_type = "JPEG"
        rf.image_compression_method = "JPEG"
    elif ext == "png":
        rf.picture_type = "PNG"
    elif ext == "gif":
        rf.picture_type = "GIF"
    elif ext in ("webp",):
        rf.picture_type = "WebP"
    return rf


def _content_facet_for_file(forensics: Dict[str, Any]) -> Optional[ContentDataFacet]:
    hashes: List[Hash] = []
    if forensics.get("sha256_hex"):
        hashes.append(
            Hash(
                hash_method=["SHA256"],
                hash_value=forensics["sha256_hex"],
            )
        )
    mime = forensics.get("mime_type")
    mime_list = [mime] if isinstance(mime, str) else []
    if not hashes and not mime_list and forensics.get("size_in_bytes") is None:
        return None
    cdf = ContentDataFacet(
        hash=hashes,
        mime_type=mime_list,
    )
    if forensics.get("size_in_bytes") is not None:
        cdf.size_in_bytes = forensics["size_in_bytes"]
    return cdf


def build_case_fragment_from_job_dict(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return JSON-LD with @context and @graph for one RescueBox job using ``CASEGraph``.

    Emits first-class ``rb:`` execution/request/result fields, explicit ``uco-action:object`` /
    ``uco-action:result`` links, optional multi-step ``InvestigativeAction`` chains, search-hit
    ``uco-core:Relationship`` nodes with rank/similarity, and raster observables where appropriate.
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
    batch_rows = _parse_batch_file_rows(response)
    output_paths = (
        [r["path"] for r in batch_rows]
        if batch_rows
        else _extract_output_paths(response)
    )
    input_dir_paths, text_inputs, params_flat = _parse_request_structure(request)

    result_id = f"kb:result-{uid}"
    prov_id = f"kb:provenance-{uid}"

    pipeline_eps = _ordered_pipeline_endpoints(str(endpoint), chain)
    n_steps = len(pipeline_eps)

    graph = CASEGraph(
        kb_prefix=KB_PREFIX,
        extra_context={
            "rb": RB_NS,
        },
    )

    tool_rb = graph.create(
        Tool,
        id="kb:tool-rescuebox",
        name="RescueBox",
        version="3.0.0",
    )

    instruments: List[Any] = []
    for ep_step in pipeline_eps:
        instruments.append(
            graph.create(
                AnalyticTool,
                id=f"kb:instrument-{_endpoint_slug(ep_step)}",
                name=ep_step,
                tool_type="RescueBox plugin endpoint",
            )
        )

    # --- Input observables (action object) ---
    input_observables: List[Any] = []
    for d in sorted(set(input_dir_paths)):
        ff = _file_facet(d, is_dir=True)
        did = _kb_id(d, "dir")
        input_observables.append(graph.create(Directory, id=did, has_facet=[ff]))

    query_text_full: Optional[str] = None
    for key, txt in text_inputs:
        if txt and "query" in key.lower():
            query_text_full = txt
            break
    if not query_text_full:
        for _key, txt in text_inputs:
            if txt:
                query_text_full = txt
                break

    if query_text_full:
        qfacet = ContentDataFacet(
            data_payload=query_text_full,
            mime_type=["text/plain"],
        )
        input_observables.append(
            graph.create(
                ContentData,
                id=f"kb:querytext-{uid}",
                name="Search query text",
                has_facet=[qfacet],
            )
        )

    input_path_files: List[str] = []
    for key, p in text_inputs:
        if ":path_file" in key:
            input_path_files.append(p)

    output_rows: List[Dict[str, Any]] = list(batch_rows)
    if not output_rows and output_paths:
        output_rows = [
            {
                "path": p,
                "rank": i + 1,
                "similarity": None,
                "model_name": None,
                "metadata": {},
            }
            for i, p in enumerate(output_paths)
        ]

    input_file_path_set = set(input_path_files)
    output_path_set = {str(r["path"]) for r in output_rows}

    file_obs_by_path: Dict[str, Any] = {}

    def _ensure_file_observable(path: str, *, as_input: bool, as_output: bool) -> Any:
        p = str(path)
        if p in file_obs_by_path:
            return file_obs_by_path[p]
        forensics = _local_file_forensics(p) if not p.endswith(os.sep) else {}
        is_raster = _is_raster_path(p) and not os.path.isdir(p)
        ff = _file_facet(p, is_dir=False, forensics=forensics)
        facets: List[Any] = [ff]
        if is_raster:
            facets.append(_raster_facet(p))
        cdf = _content_facet_for_file(forensics)
        if cdf:
            facets.append(cdf)
        ctor = RasterPicture if is_raster else File
        tags: List[str] = []
        if as_input:
            tags.append("rb:input_file")
        if as_output:
            tags.append("rb:output_file")
        out_name = Path(p).name or p
        obs = graph.create(
            ctor,
            id=_kb_id(p, "file"),
            name=out_name,
            tag=tags,
            has_facet=facets,
        )
        file_obs_by_path[p] = obs
        return obs

    for p in input_path_files:
        _ensure_file_observable(p, as_input=True, as_output=(p in output_path_set))

    for row in output_rows:
        p = str(row["path"])
        _ensure_file_observable(p, as_input=(p in input_file_path_set), as_output=True)

    output_observables: List[Any] = []
    seen_out: Set[int] = set()
    for r in output_rows:
        p = str(r["path"])
        o = _ensure_file_observable(
            p, as_input=(p in input_file_path_set), as_output=True
        )
        oid = id(o)
        if oid in seen_out:
            continue
        seen_out.add(oid)
        output_observables.append(o)

    if isinstance(response, dict):
        root = response.get("root") or response
        if not isinstance(root, dict):
            root = {}
    else:
        root = {}
    output_type = _infer_output_type_from_root(root)
    model_from_params = params_flat.get("model_name")
    if not isinstance(model_from_params, str):
        model_from_params = None

    # Primary result assertion (no JSON blobs; structured fields go on rb: after serialize)
    result_line = f"RescueBox job {uid} status={status}"
    if output_type:
        result_line += f" output_type={output_type}"
    if output_paths:
        result_line += f" artifacts={len(output_paths)}"
    result_assertion = graph.create(
        Assertion,
        id=result_id,
        name=f"RescueBox job result {uid}",
        description=[result_line],
    )

    st = _parse_datetime(str(start) if start else "")
    et = _parse_datetime(str(end) if end else "")

    step_assertions: List[Any] = []
    if n_steps > 1:
        for i in range(n_steps - 1):
            ep = pipeline_eps[i]
            step_assertions.append(
                graph.create(
                    Assertion,
                    id=f"kb:result-{uid}-step{i}",
                    name=f"Pipeline step {i + 1}/{n_steps}: {ep}",
                    description=[
                        f"Intermediate pipeline step recorded without separate response payload (endpoint {ep})."
                    ],
                )
            )

    obj_list: List[Any] = list(input_observables)
    res_list: List[Any] = [result_assertion] + output_observables

    # CASEGraph snapshots each node at ``create()`` — pass ``object``, ``result``,
    # ``was_informed_by`` in the constructor so they appear in serialized JSON-LD.
    inv_actions: List[Any] = []
    prev_inv: Optional[Any] = None
    for step_i in range(n_steps):
        if n_steps == 1:
            iid = f"kb:inv-{uid}"
        elif step_i == n_steps - 1:
            iid = f"kb:inv-{uid}"
        else:
            iid = f"kb:inv-{uid}-step{step_i}"
        ep = pipeline_eps[step_i]
        name = (
            f"RescueBox job step {step_i + 1}/{n_steps}: {ep}"
            if n_steps > 1
            else f"RescueBox job: {ep or 'unknown'}"
        )
        ia_kwargs: Dict[str, Any] = {
            "id": iid,
            "name": name,
            "description": [f"Endpoint {ep} for job {uid}."],
            "performer": tool_rb,
            "instrument": [instruments[step_i]],
            "action_status": [action_status],
            "start_time": st,
            "end_time": et,
        }
        if prev_inv is not None:
            ia_kwargs["was_informed_by"] = [prev_inv]
        if n_steps == 1:
            ia_kwargs["object"] = obj_list
            ia_kwargs["result"] = res_list
        elif step_i == n_steps - 1:
            ia_kwargs["object"] = obj_list
            ia_kwargs["result"] = res_list
        else:
            ia_kwargs["object"] = list(input_observables) if step_i == 0 else []
            ia_kwargs["result"] = [step_assertions[step_i]]
        inv = graph.create(InvestigativeAction, **ia_kwargs)
        inv_actions.append(inv)
        prev_inv = inv

    primary_inv = inv_actions[-1]

    # Search-hit relationships (primary action -> each ranked output file observable)
    hit_relationships: List[Any] = []
    for i, row in enumerate(output_rows):
        p = str(row["path"])
        tgt = file_obs_by_path.get(p)
        if tgt is None:
            continue
        rel = graph.create(
            Relationship,
            id=f"kb:rel-hit-{uid}-{i}",
            is_directional=True,
            kind_of_relationship="SearchResultMatch",
            source=[primary_inv],
            target=tgt,
        )
        hit_relationships.append(rel)

    dir_paths: Set[str] = set(input_dir_paths)
    for op in output_paths:
        try:
            parent = str(Path(op).parent)
            if parent and parent != op:
                dir_paths.add(parent)
        except Exception:
            pass

    extra_dirs: List[Any] = []
    for d in sorted(dir_paths):
        if d in input_dir_paths:
            continue
        ff = _file_facet(d, is_dir=True)
        extra_dirs.append(graph.create(Directory, id=_kb_id(d, "dir"), has_facet=[ff]))

    # Provenance bundle
    prov_objects: List[Any] = []
    prov_objects.extend(inv_actions)
    prov_objects.append(result_assertion)
    prov_objects.extend(step_assertions)
    prov_objects.append(tool_rb)
    prov_objects.extend(instruments)
    prov_objects.extend(input_observables)
    prov_objects.extend(extra_dirs)
    prov_objects.extend(output_observables)
    prov_objects.extend(hit_relationships)

    graph.create(
        ProvenanceRecord,
        id=prov_id,
        exhibit_number=f"RB-JOB-{uid}",
        description=[
            "Provenance bundle linking RescueBox investigative actions to observables."
        ],
        object=prov_objects,
    )

    doc = json.loads(graph.serialize())

    # --- Post-process: rb: first-class fields (avoid JSON-in-string for core facts) ---
    chain_list: List[str] = [str(x) for x in chain] if isinstance(chain, list) else []
    structured_action: Dict[str, Any] = {
        "rb:jobUid": uid,
        "rb:endpoint": str(endpoint),
        "rb:endpointChain": chain_list,
        "rb:jobStatus": status,
        "rb:actionStatus": action_status,
        "rb:outputType": output_type,
        "rb:requestParameters": params_flat,
        "rb:inputDirectoryPaths": sorted(set(input_dir_paths)),
        "rb:inputQueryText": query_text_full,
        "rb:artifactPaths": output_paths,
        "rb:artifactCount": len(output_paths),
        "rb:pipelineStepCount": n_steps,
    }
    if model_from_params:
        structured_action["rb:modelName"] = model_from_params
    for k in ("top_k", "min_similarity"):
        if k in params_flat:
            structured_action[f"rb:{k}"] = params_flat[k]

    primary_id = graph.get_id(primary_inv) or f"kb:inv-{uid}"
    for node in doc.get("@graph", []):
        if node.get("@id") != primary_id:
            continue
        for k, v in structured_action.items():
            node[k] = v
        node["rb:requestSummary"] = req_summary
        node["rb:outputSummary"] = out_summary
        break

    # Result assertion: structured summary only (no embedded JSON)
    for node in doc.get("@graph", []):
        if node.get("@id") == result_id:
            node["rb:outputType"] = output_type
            node["rb:artifactCount"] = len(output_paths)
            node["rb:artifactPaths"] = output_paths
            break

    # Relationship enrichment: rank / similarity / model
    rel_idx = 0
    for node in doc.get("@graph", []):
        nid = node.get("@id") or ""
        if not nid.startswith(f"kb:rel-hit-{uid}-"):
            continue
        if rel_idx >= len(output_rows):
            break
        row = output_rows[rel_idx]
        node["rb:searchHitRank"] = row.get("rank")
        if row.get("similarity") is not None:
            node["rb:similarityScore"] = row["similarity"]
        mod = row.get("model_name") or model_from_params
        if mod:
            node["rb:matchModel"] = mod
        node["rb:matchDisposition"] = "matched_by_semantic_search"
        rel_idx += 1

    # Per-hit observable enrichment
    for i, row in enumerate(output_rows):
        p = str(row["path"])
        oid = _kb_id(p, "file")
        for node in doc.get("@graph", []):
            if node.get("@id") != oid:
                continue
            node["rb:searchHitRank"] = row.get("rank")
            if row.get("similarity") is not None:
                node["rb:similarityScore"] = row["similarity"]
            mod = row.get("model_name") or model_from_params
            if mod:
                node["rb:matchModel"] = mod
            if params_flat.get("min_similarity") is not None:
                node["rb:minSimilarityThreshold"] = params_flat.get("min_similarity")
            break

    ctx = doc.setdefault("@context", {})
    if isinstance(ctx, dict):
        ctx["rb"] = RB_NS

    return doc


def build_jsonld_text(job: Dict[str, Any]) -> str:
    doc = build_case_fragment_from_job_dict(job)
    doc = _json_safe(doc)
    return json.dumps(doc, indent=2, ensure_ascii=False)
