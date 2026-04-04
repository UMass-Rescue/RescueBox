from typing import TypedDict, NotRequired
import json
import logging
import os

import typer
from rb.lib.ml_service import MLService
from rb.lib.utils import apply_torch_cpu_preference
from rb.api.models import (
    FloatRangeDescriptor,
    InputSchema,
    InputType,
    IntRangeDescriptor,
    ParameterSchema,
    RangedFloatParameterDescriptor,
    RangedIntParameterDescriptor,
    ResponseBody,
    TaskSchema,
    DirectoryInput,
    TextInput,
    TextResponse,
    BatchFileInput,
)

#_MODEL_NAME = "BAAI/bge-small-en-v1.5"
_MODEL_NAME = "BAAI/bge-m3"

_BGE_QUERY_PREFIX = "query: "  # BGE asymmetric search (queries only)

_CHUNKER = "langchain"
_CHUNK_SIZE = 300
_CHUNK_OVERLAP = 60

# Forensic safety: never read an entire multi-GB log into RAM at once.
_MAX_READ_BYTES_PER_FILE = 50 * 1024 * 1024  # 50 MiB per file (truncate with warning)
# GPU batching: one encode() over all chunks; raise on high-end GPUs (e.g. Spark / Blackwell).
_EMBED_BATCH_SIZE = 256
from rb.api.database import engine, TextEmbeddingChunk
from sqlalchemy import bindparam, text as sql_text, update
from sqlmodel import Session
from sqlmodel import delete, select

APP_NAME = "text_embeddings"
logger = logging.getLogger(__name__)


class Inputs(TypedDict):
    input_dir: DirectoryInput
    query: TextInput


class Parameters(TypedDict):
    top_k: int
    min_similarity: NotRequired[float]


def task_schema() -> TaskSchema:
    input_dir_schema = InputSchema(
        key="input_dir",
        label="Directory of text files to search",
        input_type=InputType.DIRECTORY,
    )
    query_schema = InputSchema(
        key="query",
        label="Search query",
        input_type=InputType.TEXT,
    )

    top_k_desc = RangedIntParameterDescriptor(
        range=IntRangeDescriptor(min=1, max=20),
        default=5,
    )
    min_similarity_desc = RangedFloatParameterDescriptor(
        range=FloatRangeDescriptor(min=0.0, max=1.0),
        default=0.5,
    )

    return TaskSchema(
        inputs=[input_dir_schema, query_schema],
        parameters=[
            ParameterSchema(
                key="top_k",
                label="Top K results",
                subtitle="Number of most similar results to return",
                value=top_k_desc,
            ),
            ParameterSchema(
                key="min_similarity",
                label="Match threshold",
                subtitle="Similarity >= this value counts as a match (0.5 typical, 0.12/0.19 = weak)",
                value=min_similarity_desc,
            ),
        ],
    )


server = MLService(APP_NAME)

script_dir = os.path.dirname(os.path.abspath(__file__))
info_file_path = os.path.join(script_dir, "app-info.md")
with open(info_file_path, "r") as f:
    info = f.read()

server.add_app_metadata(
    plugin_name=APP_NAME,
    name="Search Text",
    author="UMass RescueLab",
    version="3.0.0",
    info=info,
    gpu=True,
)


def _chunk_text(
    text: str,
    *,
    chunker: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    if chunker == "langchain":
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter  # type: ignore
        except Exception as exc:  # pragma: no cover - import guard
            raise ValueError(
                "LangChain text splitters not available. Please install 'langchain-text-splitters'."
            ) from exc
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        return splitter.split_text(text)
    elif chunker == "llamaindex":
        try:
            from llama_index.core.node_parser import SentenceSplitter  # type: ignore
        except Exception as exc:  # pragma: no cover - import guard
            raise ValueError(
                "LlamaIndex not available. Please install 'llama-index-core' to use this chunker."
            ) from exc
        splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return splitter.split_text(text)
    else:
        return [text]


def _truncate(text: str, max_len: int) -> str:
    s = text.strip()
    return s[:max_len] + ("..." if len(s) > max_len else "")


def _read_text_file_safe(path: str, max_bytes: int) -> str:
    """Read text with a hard byte cap so huge forensic files cannot OOM the host."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read(max_bytes + 1)
        if len(data) > max_bytes:
            logger.warning(
                "Truncating %s to %d bytes for embedding (size cap)",
                path,
                max_bytes,
            )
            return data[:max_bytes]
        return data
    except OSError as exc:
        logger.warning("Skip unreadable file %s: %s", path, exc)
        return ""


def _format_search_query(model_name: str, query_text: str) -> str:
    """
    Encode-time string for the search query only. Document chunks are passed raw (no prefix).
    Qwen3 retrieval models expect an instruction-wrapped query; BGE uses a short asymmetric prefix.
    """
    if "qwen" in model_name.lower():
        return (
            "Instruct: Given a web search query, retrieve relevant passages that answer the query\n"
            f"Query: {query_text}"
        )
    return f"{_BGE_QUERY_PREFIX}{query_text}"


def _paths_with_chunks_for_params(
    session, paths: list[str], model_name: str, chunk_size: int, chunk_overlap: int
) -> set[str]:
    """Paths in ``paths`` that already have at least one stored chunk for this model + chunk params."""
    if not paths:
        return set()
    rows = session.exec(
        select(TextEmbeddingChunk.path).where(
            TextEmbeddingChunk.path.in_(paths),
            TextEmbeddingChunk.model_name == model_name,
            TextEmbeddingChunk.chunk_size == chunk_size,
            TextEmbeddingChunk.chunk_overlap == chunk_overlap,
        ).distinct()
    ).all()
    return set(rows)


def _delete_chunks_for_paths(session, paths: list[str], model_name: str) -> None:
    """Delete chunks for these paths and model so they can be re-embedded."""
    session.execute(
        delete(TextEmbeddingChunk).where(
            TextEmbeddingChunk.path.in_(paths),
            TextEmbeddingChunk.model_name == model_name,
        )
    )


def _basename_key(path: str) -> str:
    """Normalized basename for moved-file reuse (case-folded)."""
    return os.path.basename(os.path.normpath(path)).casefold()


def _relocate_matching_basenames(
    session,
    file_paths: list[str],
    model_name: str,
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    """
    When the full path changes but the filename matches stored rows for this model and chunk
    params, update stored ``path`` to the new location so vectors are not recomputed.

    If two different files share the same basename, embeddings may be reused incorrectly.
    Relocation is skipped when both the old and new full paths appear in ``file_paths``.
    """
    stored_paths = session.exec(
        select(TextEmbeddingChunk.path).where(
            TextEmbeddingChunk.model_name == model_name,
            TextEmbeddingChunk.chunk_size == chunk_size,
            TextEmbeddingChunk.chunk_overlap == chunk_overlap,
        ).distinct()
    ).all()
    by_bn: dict[str, str] = {}
    for sp in stored_paths:
        bn = _basename_key(sp)
        if bn not in by_bn:
            by_bn[bn] = sp

    existing_exact = _paths_with_chunks_for_params(
        session, file_paths, model_name, chunk_size, chunk_overlap
    )
    file_paths_set = set(file_paths)

    for fp in file_paths:
        if fp in existing_exact:
            continue
        bn = _basename_key(fp)
        old_path = by_bn.get(bn)
        if old_path is None or old_path == fp:
            continue
        if old_path in file_paths_set:
            continue
        session.execute(
            update(TextEmbeddingChunk)
            .where(
                TextEmbeddingChunk.path == old_path,
                TextEmbeddingChunk.model_name == model_name,
                TextEmbeddingChunk.chunk_size == chunk_size,
                TextEmbeddingChunk.chunk_overlap == chunk_overlap,
            )
            .values(path=fp)
        )
        logger.info(
            "Reused embeddings by basename match: %s -> %s (basename %r)",
            old_path,
            fp,
            bn,
        )
        by_bn[bn] = fp


def _collect_text_files(input_dir: str) -> list[str]:
    """Return sorted list of text file paths in the directory."""
    allowed_exts = {".txt", ".text", ".md", ".log"}
    paths = []
    for name in sorted(os.listdir(input_dir)):
        path = os.path.join(input_dir, name)
        if os.path.isfile(path) and os.path.splitext(path)[1].lower() in allowed_exts:
            paths.append(path)
    return paths


def search(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    """
    Semantic search over text files. Embeds the directory if embeddings don't exist
    for the requested model, then runs cosine similarity search.
    """
    apply_torch_cpu_preference()
    import torch
    from sentence_transformers import SentenceTransformer  # type: ignore

    input_dir = str(inputs["input_dir"].path)
    query_text = inputs["query"].text
    model_name = _MODEL_NAME
    top_k = int(parameters.get("top_k", 5))
    min_similarity = float(parameters.get("min_similarity", 0.5))

    # Use file_filter when provided (e.g. from image_summary pipeline); else scan input_dir
    file_paths: list[str] = []
    if "file_filter" in inputs and inputs.get("file_filter"):
        ff = inputs["file_filter"]
        files = getattr(ff, "files", None) or (ff if isinstance(ff, dict) else {}).get("files", [])
        if files:
            for f in files:
                p = f.get("path") if isinstance(f, dict) else getattr(f, "path", None)
                if p and isinstance(p, str) and os.path.isfile(p):
                    file_paths.append(p)
    if not file_paths:
        file_paths = _collect_text_files(input_dir)
    if not file_paths:
        return ResponseBody(
            root=TextResponse(
                value=json.dumps({"error": "No text files found in directory", "results": []}),
                title="Text Search",
                subtitle="No text files to search",
            )
        )

    cuda_ok = torch.cuda.is_available()
    mps_ok = bool(getattr(torch.backends, "mps", None)) and torch.backends.mps.is_available()
    if cuda_ok:
        device = torch.device("cuda")
    elif mps_ok:
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    logger.info(
        "SentenceTransformer runtime: cuda_available=%s mps_available=%s -> selected device=%s",
        cuda_ok,
        mps_ok,
        device,
    )
    if cuda_ok and device.type == "cuda":
        try:
            idx = torch.cuda.current_device()
            logger.info(
                "CUDA GPU in use: name=%s index=%s",
                torch.cuda.get_device_name(idx),
                idx,
            )
        except Exception as e:
            logger.debug("Could not read CUDA device name: %s", e)
    elif device.type == "mps":
        logger.info("Apple Metal (MPS) in use for SentenceTransformer")

    model = SentenceTransformer(model_name, device=str(device))
    try:
        param_dev = next(model.parameters()).device
    except Exception:
        param_dev = device
    logger.info(
        "SentenceTransformer loaded on device=%s (parameter device=%s) model_name=%s",
        device,
        param_dev,
        model_name,
    )

    with Session(engine) as session:
        _relocate_matching_basenames(
            session, file_paths, model_name, _CHUNK_SIZE, _CHUNK_OVERLAP
        )
        session.flush()

        existing_paths = _paths_with_chunks_for_params(
            session, file_paths, model_name, _CHUNK_SIZE, _CHUNK_OVERLAP
        )
        paths_to_embed = [p for p in file_paths if p not in existing_paths]

        # 1) Collect chunk texts only for paths that need vectors, then 2) one batched encode.
        chunk_rows: list[tuple[str, int, str]] = []
        for path in paths_to_embed:
            text = _read_text_file_safe(path, _MAX_READ_BYTES_PER_FILE)
            if not text.strip():
                continue
            chunks = _chunk_text(
                text,
                chunker=_CHUNKER,
                chunk_size=_CHUNK_SIZE,
                chunk_overlap=_CHUNK_OVERLAP,
            )
            for idx, chunk_text in enumerate(chunks):
                chunk_rows.append((path, idx, chunk_text))

        if chunk_rows:
            texts = [row[2] for row in chunk_rows]
            logger.info(
                "Embedding %d chunks from %d file(s) (%d already had embeddings; %d total in request), "
                "batch_size=%d",
                len(texts),
                len(paths_to_embed),
                len(existing_paths),
                len(file_paths),
                _EMBED_BATCH_SIZE,
            )
            vectors = model.encode(
                texts,
                batch_size=_EMBED_BATCH_SIZE,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=len(texts) > 64,
            )
            records: list[TextEmbeddingChunk] = []
            for (path, idx, chunk_text), vec in zip(chunk_rows, vectors):
                records.append(
                    TextEmbeddingChunk(
                        path=path,
                        chunk_index=idx,
                        chunk_text=chunk_text,
                        model_name=model_name,
                        chunk_size=_CHUNK_SIZE,
                        chunk_overlap=_CHUNK_OVERLAP,
                        embedding=vec.tolist(),
                    )
                )
            session.add_all(records)
        session.commit()

        # Search: query-side instruction only (Qwen) or BGE asymmetric prefix — not applied to stored chunks.
        search_query = _format_search_query(model_name, query_text)
        query_embedding = model.encode(
            search_query,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        embedding_str = "[" + ",".join(str(x) for x in query_embedding.tolist()) + "]"

        # One row per file: best-matching chunk only (DISTINCT ON), then top_k files by similarity.
        # Scope to this request's paths so we do not rank unrelated corpus rows.
        query_sql = sql_text(
            f"""
            SELECT * FROM (
                SELECT DISTINCT ON (path)
                    id,
                    path,
                    chunk_index,
                    chunk_text,
                    1 - (embedding <=> '{embedding_str}'::vector) AS similarity
                FROM text_embedding_chunks
                WHERE model_name = :model_name
                  AND chunk_size = :chunk_size
                  AND chunk_overlap = :chunk_overlap
                  AND path IN :paths
                ORDER BY path, embedding <=> '{embedding_str}'::vector ASC
            ) AS best_chunk_per_path
            ORDER BY similarity DESC
            LIMIT :top_k
            """
        ).bindparams(bindparam("paths", expanding=True))
        rows = session.execute(
            query_sql,
            {
                "model_name": model_name,
                "chunk_size": _CHUNK_SIZE,
                "chunk_overlap": _CHUNK_OVERLAP,
                "paths": file_paths,
                "top_k": top_k,
            },
        ).fetchall()

    search_results = []
    for row in rows:
        sim = float(row.similarity)
        search_results.append({
            "id": row.id,
            "path": row.path,
            "chunk_index": row.chunk_index,
            "similarity": round(sim, 4),
            "is_match": sim >= min_similarity,
            "matching_text": _truncate(row.chunk_text or "", 600),
        })
    response_data = {
        "query": query_text,
        "model": model_name,
        "top_k": top_k,
        "min_similarity": min_similarity,
        "similarity_guidance": (
            f"Results with similarity >= {min_similarity} are marked as matches."
        ),
        "results": search_results,
    }

    return ResponseBody(
        root=TextResponse(
            value=json.dumps(response_data, indent=2),
            title="Text Search Results",
            subtitle=f"Found {len(search_results)} results using {model_name}",
        )
    )


def inputs_cli_parse(value: str) -> Inputs:
    # Expect "directory_path,query_text" or just directory for backwards compat
    parts = [p.strip() for p in value.split(",", 1)]
    from pathlib import Path
    input_dir = Path(parts[0]) if parts[0] else Path(".")
    query_text = parts[1] if len(parts) > 1 else ""
    return Inputs(
        input_dir=DirectoryInput(path=input_dir),
        query=TextInput(text=query_text),
    )


def parameters_cli_parse(value: str) -> Parameters:
    parts = [p.strip() for p in value.split(",")]
    top_k = int(parts[0]) if len(parts) > 0 and parts[0] else 3
    min_similarity = float(parts[1]) if len(parts) > 1 and parts[1] else 0.5
    return Parameters(top_k=top_k, min_similarity=min_similarity)


server.add_ml_service(
    rule="/search",
    ml_function=search,
    inputs_cli_parser=typer.Argument(
        parser=inputs_cli_parse,
        help="Directory path,query text (e.g. /path/to/docs,search query)",
    ),
    parameters_cli_parser=typer.Argument(
        parser=parameters_cli_parse,
        help="top_k,min_similarity (e.g. 5,0.5)",
    ),
    short_title="Search Text",
    order=0,
    task_schema_func=task_schema,
)


app = server.app
if __name__ == "__main__":
    app()
