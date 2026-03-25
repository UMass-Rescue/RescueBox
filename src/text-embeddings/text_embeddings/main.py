from typing import TypedDict, NotRequired
import json
import os

import typer
from rb.lib.ml_service import MLService
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

# Fixed defaults for demo (hidden from UI - suitable for investigators)
# BAAI/bge-small-en-v1.5: add "query: " prefix for asymmetric search
# 300/60: passes synonym (stones↔pebbles, companion↔friends) and antonym (enemy↔friends)
_MODEL_NAME = "BAAI/bge-small-en-v1.5"
_BGE_QUERY_PREFIX = "query: "  # required for BGE asymmetric search
_CHUNKER = "langchain"
_CHUNK_SIZE = 300
_CHUNK_OVERLAP = 60
from rb.api.database import engine, TextEmbeddingChunk
from sqlmodel import Session
from sqlmodel import delete, select

APP_NAME = "text_embeddings"


class Inputs(TypedDict):
    input_dir: DirectoryInput
    query: TextInput
    file_filter: NotRequired[BatchFileInput]  # Optional: from chained image_summary output


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
    file_filter_schema = InputSchema(
        key="file_filter",
        label="Optional: specific files from previous step (e.g. image summaries)",
        input_type=InputType.BATCHFILE,
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
        inputs=[input_dir_schema, query_schema, file_filter_schema],
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
    name="Text Embeddings",
    author="UMass Rescue",
    version="2.1.0",
    info=info,
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


def _has_chunks_for_paths(
    session, paths: list[str], model_name: str, chunk_size: int, chunk_overlap: int
) -> bool:
    """True if all paths have chunks for this model and chunk params (else need re-embed)."""
    if not paths:
        return False
    existing = set(
        session.exec(
            select(TextEmbeddingChunk.path).where(
                TextEmbeddingChunk.path.in_(paths),
                TextEmbeddingChunk.model_name == model_name,
                TextEmbeddingChunk.chunk_size == chunk_size,
                TextEmbeddingChunk.chunk_overlap == chunk_overlap,
            ).distinct()
        ).all()
    )
    return existing >= set(paths)


def _delete_chunks_for_paths(session, paths: list[str], model_name: str) -> None:
    """Delete chunks for these paths and model so they can be re-embedded."""
    session.execute(
        delete(TextEmbeddingChunk).where(
            TextEmbeddingChunk.path.in_(paths),
            TextEmbeddingChunk.model_name == model_name,
        )
    )


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
    import numpy as np
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

    model = SentenceTransformer(model_name)

    with Session(engine) as session:
        # Chunk-level storage: re-embed if model or chunk params changed
        if not _has_chunks_for_paths(
            session, file_paths, model_name, _CHUNK_SIZE, _CHUNK_OVERLAP
        ):
            _delete_chunks_for_paths(session, file_paths, model_name)
            for path in file_paths:
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        text = f.read()
                except Exception:
                    continue
                chunks = _chunk_text(
                    text,
                    chunker=_CHUNKER,
                    chunk_size=_CHUNK_SIZE,
                    chunk_overlap=_CHUNK_OVERLAP,
                )
                if not chunks:
                    continue
                vectors = model.encode(
                    chunks,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                for idx, (chunk_text, vec) in enumerate(zip(chunks, vectors)):
                    rec = TextEmbeddingChunk(
                        path=path,
                        chunk_index=idx,
                        chunk_text=chunk_text,
                        model_name=model_name,
                        chunk_size=_CHUNK_SIZE,
                        chunk_overlap=_CHUNK_OVERLAP,
                        embedding=vec.tolist(),
                    )
                    session.add(rec)
            session.commit()

        # Search chunks: BGE expects "query: " prefix for asymmetric search
        search_query = f"{_BGE_QUERY_PREFIX}{query_text}" if _BGE_QUERY_PREFIX else query_text
        query_embedding = model.encode(
            search_query,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        embedding_str = "[" + ",".join(str(x) for x in query_embedding.tolist()) + "]"

        from sqlalchemy import text as sql_text

        query_sql = sql_text(f"""
            SELECT
                id,
                path,
                chunk_index,
                chunk_text,
                1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM text_embedding_chunks
            WHERE model_name = :model_name
              AND chunk_size = :chunk_size
              AND chunk_overlap = :chunk_overlap
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT :top_k
        """)
        rows = session.execute(
            query_sql,
            {
                "model_name": model_name,
                "chunk_size": _CHUNK_SIZE,
                "chunk_overlap": _CHUNK_OVERLAP,
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
            f"Results with similarity >= {min_similarity} are marked as matches. "
            
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
