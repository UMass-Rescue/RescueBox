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
    TextResponse,
)
from rb.api.database import engine, TextEmbedding
from sqlmodel import Session

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
            results[path] = file_embedding.tolist()
            session.add(TextEmbedding(path=path, embedding=file_embedding.tolist()))
        session.commit()

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


app = server.app
if __name__ == "__main__":
    app()


