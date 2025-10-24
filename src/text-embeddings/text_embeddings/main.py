from typing import TypedDict
import json

import typer
from rb.lib.ml_service import MLService
from rb.api.models import (
    InputSchema,
    InputType,
    ParameterSchema,
    EnumParameterDescriptor,
    EnumVal,
    RangedIntParameterDescriptor,
    IntRangeDescriptor,
    ResponseBody,
    TaskSchema,
    DirectoryInput,
    TextInput,
    TextResponse,
)
from rb.api.database import engine, TextEmbedding
from rb.api.embedding_storage import TextEmbeddingStorage
from sqlmodel import Session, select

APP_NAME = "text_embeddings"


class Inputs(TypedDict):
    input_dir: DirectoryInput


class Parameters(TypedDict):
    model_name: str
    chunker: str
    chunk_size: int
    chunk_overlap: int


def task_schema() -> TaskSchema:
    text_schema = InputSchema(
        key="input_dir",
        label="Provide directory of text files",
        input_type=InputType.DIRECTORY,
    )

    model_enum = EnumParameterDescriptor(
        enum_vals=[
            EnumVal(key="all-MiniLM-L6-v2", label="all-MiniLM-L6-v2"),
            EnumVal(key="all-mpnet-base-v2", label="all-mpnet-base-v2"),
            EnumVal(key="multi-qa-MiniLM-L6-cos-v1", label="multi-qa-MiniLM-L6-cos-v1"),
        ],
        default="all-MiniLM-L6-v2",
    )

    chunker_enum = EnumParameterDescriptor(
        enum_vals=[
            EnumVal(key="langchain", label="LangChain RecursiveCharacterTextSplitter"),
            EnumVal(key="llamaindex", label="LlamaIndex SentenceSplitter"),
        ],
        default="langchain",
    )

    chunk_size_desc = RangedIntParameterDescriptor(
        range=IntRangeDescriptor(min=600, max=800),
        default=800,
    )
    chunk_overlap_desc = RangedIntParameterDescriptor(
        range=IntRangeDescriptor(min=60, max=120),
        default=100,
    )

    return TaskSchema(
        inputs=[text_schema],
        parameters=[
            ParameterSchema(
                key="model_name",
                label="SentenceTransformer model",
                subtitle="Hugging Face model to compute embeddings",
                value=model_enum,
            ),
            ParameterSchema(
                key="chunker",
                label="Chunking strategy",
                subtitle="Choose the library used to split text",
                value=chunker_enum,
            ),
            ParameterSchema(
                key="chunk_size",
                label="Chunk size",
                subtitle="Target characters per chunk",
                value=chunk_size_desc,
            ),
            ParameterSchema(
                key="chunk_overlap",
                label="Chunk overlap",
                subtitle="Characters to overlap between chunks",
                value=chunk_overlap_desc,
            ),
        ],
    )


server = MLService(APP_NAME)
server.add_app_metadata(
    plugin_name=APP_NAME,
    name="Text Embeddings",
    author="UMass Rescue",
    version="2.1.0",
    info="Create embeddings for input text with optional chunking.",
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


def embed_text(inputs: Inputs, parameters: Parameters) -> ResponseBody:
    import os
    import numpy as np

    input_dir = str(inputs["input_dir"].path)
    model_name = parameters.get("model_name", "all-MiniLM-L6-v2")
    chunker = parameters.get("chunker", "langchain")
    chunk_size = int(parameters.get("chunk_size", 800))
    chunk_overlap = int(parameters.get("chunk_overlap", 100))

    from sentence_transformers import SentenceTransformer  # type: ignore

    model = SentenceTransformer(model_name)

    allowed_exts = {".txt", ".text", ".md", ".log"}
    file_paths: list[str] = []
    for name in sorted(os.listdir(input_dir)):
        path = os.path.join(input_dir, name)
        if os.path.isfile(path) and os.path.splitext(path)[1].lower() in allowed_exts:
            file_paths.append(path)

    results: dict[str, list[float]] = {}
    with Session(engine) as session:
        storage = TextEmbeddingStorage(session)
        
        for path in file_paths:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except Exception:
                continue

            chunks = _chunk_text(
                text,
                chunker=chunker,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            if not chunks:
                continue

            vectors = model.encode(
                chunks,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            file_embedding = np.mean(vectors, axis=0)
            embedding_list = file_embedding.tolist()
            results[path] = embedding_list
            
            # Save to database using storage interface
            storage.save_embedding(path, embedding_list)
        
        # Commit all embeddings at once
        storage.commit()

    response = TextResponse(
        value=json.dumps(results),
        title="Text Embeddings",
        subtitle=f"files={len(results)}, model={model_name}, chunker={chunker}, size={chunk_size}, overlap={chunk_overlap}",
    )
    return ResponseBody(root=response)


def inputs_cli_parse(value: str) -> Inputs:
    return Inputs(input_dir=DirectoryInput(path=value))


def parameters_cli_parse(value: str) -> Parameters:
    # Accept comma-separated values: model_name,chunker,chunk_size,chunk_overlap
    parts = [p.strip() for p in value.split(",")]
    model_name = parts[0] if len(parts) > 0 and parts[0] else "all-MiniLM-L6-v2"
    chunker = parts[1] if len(parts) > 1 and parts[1] else "langchain"
    chunk_size = int(parts[2]) if len(parts) > 2 and parts[2] else 500
    chunk_overlap = int(parts[3]) if len(parts) > 3 and parts[3] else 50
    return Parameters(
        model_name=model_name,
        chunker=chunker,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


server.add_ml_service(
    rule="/embed_text",
    ml_function=embed_text,
    inputs_cli_parser=typer.Argument(parser=inputs_cli_parse, help="Directory of text files"),
    parameters_cli_parser=typer.Argument(
        parser=parameters_cli_parse,
        help="model_name,chunker,chunk_size,chunk_overlap",
    ),
    short_title="Text Embeddings",
    order=0,
    task_schema_func=task_schema,
)


# ============================================================================
# Search Endpoint
# ============================================================================

class SearchInputs(TypedDict):
    query: TextInput


class SearchParameters(TypedDict):
    model_name: str
    top_k: int


def search_task_schema() -> TaskSchema:
    query_schema = InputSchema(
        key="query",
        label="Search query",
        input_type=InputType.TEXT,
    )

    model_enum = EnumParameterDescriptor(
        enum_vals=[
            EnumVal(key="all-MiniLM-L6-v2", label="all-MiniLM-L6-v2"),
            EnumVal(key="all-mpnet-base-v2", label="all-mpnet-base-v2"),
            EnumVal(key="multi-qa-MiniLM-L6-cos-v1", label="multi-qa-MiniLM-L6-cos-v1"),
        ],
        default="all-MiniLM-L6-v2",
    )

    top_k_desc = RangedIntParameterDescriptor(
        range=IntRangeDescriptor(min=1, max=20),
        default=5,
    )

    return TaskSchema(
        inputs=[query_schema],
        parameters=[
            ParameterSchema(
                key="model_name",
                label="SentenceTransformer model",
                subtitle="Must match the model used for embedding",
                value=model_enum,
            ),
            ParameterSchema(
                key="top_k",
                label="Top K results",
                subtitle="Number of most similar results to return",
                value=top_k_desc,
            ),
        ],
    )


def search_text(inputs: SearchInputs, parameters: SearchParameters) -> ResponseBody:
    """
    Search for similar text embeddings using pgvector cosine similarity.
    
    Uses optimized vector similarity search with the <=> operator which computes
    cosine distance (1 - cosine similarity) efficiently in PostgreSQL.
    """
    import numpy as np
    from sentence_transformers import SentenceTransformer  # type: ignore

    query_text = inputs["query"].text
    model_name = parameters.get("model_name", "all-MiniLM-L6-v2")
    top_k = int(parameters.get("top_k", 5))

    # Load model and generate query embedding
    model = SentenceTransformer(model_name)
    query_embedding = model.encode(
        query_text,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    # Search using pgvector's optimized cosine distance operator
    with Session(engine) as session:
        # Use raw SQL for pgvector's <=> operator (cosine distance)
        # cosine_distance = 1 - cosine_similarity
        # So we convert back: similarity = 1 - distance
        from sqlalchemy import text as sql_text
        
        # Convert embedding to proper format for pgvector
        embedding_str = "[" + ",".join(str(x) for x in query_embedding.tolist()) + "]"
        
        query = sql_text(f"""
            SELECT 
                id,
                path,
                1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM text_embeddings
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT :top_k
        """)
        
        results = session.execute(
            query,
            {
                "top_k": top_k
            }
        ).fetchall()

    # Format results
    search_results = []
    for row in results:
        search_results.append({
            "id": row.id,
            "path": row.path,
            "similarity": float(row.similarity),
        })

    response_data = {
        "query": query_text,
        "model": model_name,
        "top_k": top_k,
        "results": search_results,
    }

    response = TextResponse(
        value=json.dumps(response_data, indent=2),
        title="Text Search Results",
        subtitle=f"Found {len(search_results)} results using {model_name}",
    )
    return ResponseBody(root=response)


def search_inputs_cli_parse(value: str) -> SearchInputs:
    return SearchInputs(query=TextInput(text=value))


def search_parameters_cli_parse(value: str) -> SearchParameters:
    # Accept comma-separated values: model_name,top_k
    parts = [p.strip() for p in value.split(",")]
    model_name = parts[0] if len(parts) > 0 and parts[0] else "all-MiniLM-L6-v2"
    top_k = int(parts[1]) if len(parts) > 1 and parts[1] else 5
    return SearchParameters(
        model_name=model_name,
        top_k=top_k,
    )


server.add_ml_service(
    rule="/search_text",
    ml_function=search_text,
    inputs_cli_parser=typer.Argument(parser=search_inputs_cli_parse, help="Search query text"),
    parameters_cli_parser=typer.Argument(
        parser=search_parameters_cli_parse,
        help="model_name,top_k",
    ),
    short_title="Search Text Embeddings",
    order=1,
    task_schema_func=search_task_schema,
)


app = server.app
if __name__ == "__main__":
    app()


