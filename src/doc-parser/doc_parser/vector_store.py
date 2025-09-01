import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
from typing import Dict, List, Tuple
import whoosh.index
import os
import tempfile
import ollama
from langchain.text_splitter import MarkdownHeaderTextSplitter, PythonCodeTextSplitter, RecursiveCharacterTextSplitter
from langchain.schema import Document
import whoosh.index
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser, syntax
from whoosh.query import Term

# 1. Initialize SentenceTransformer models
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

# 2. Initialize ChromaDB client
client = chromadb.Client()
collection = client.get_or_create_collection("rescuebox-docs")

# 3. Initialize Whoosh index
schema = Schema(
    title=TEXT(stored=True),
    content=TEXT(stored=True),
    parent_id=ID(stored=True),
    id=ID(unique=True, stored=True),
)
whoosh_dir = os.path.join(tempfile.gettempdir(), "rescuebox_whoosh_index")


def get_whoosh_index():
    if not os.path.exists(whoosh_dir):
        os.makedirs(whoosh_dir)

    if whoosh.index.exists_in(whoosh_dir):
        return whoosh.index.open_dir(whoosh_dir)
    else:
        return whoosh.index.create_in(whoosh_dir, schema)


def create_vector_store(docs: Dict[str, str]):
    """
    Creates a vector store from the documentation.

    Args:
        docs: A dictionary of documentation, with page titles as keys and content as values.
    """
    if not docs:
        return

    ix = get_whoosh_index()
    writer = ix.writer()
    headers_to_split_on = [
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on
    )

    chunks = []
    chunk_counter = 0
    for title, content in docs.items():
        print(f"Processing {title}...{content[:40]}...")  # Print first 40 chars for debugging
        if title.endswith(".py"):
           python_splitter = PythonCodeTextSplitter()
           md_header_splits = python_splitter.split_text(content)
        else:
            headers_to_split_on = [
                ("##", "Header 2"),
                ("###", "Header 3"),
                ("####", "Header 4"),
            ]
            markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on
            )
            md_header_splits = markdown_splitter.split_text(content)

        parent_chunk_id = None
        for chunk in md_header_splits:
            if isinstance(chunk, str):
                chunk = Document(page_content=chunk)

            chunk_id = f"{title}-{chunk_counter}"
            chunk_counter += 1

            metadata = {"title": title}
            metadata.update(chunk.metadata)

            chunks.append(
                {
                    "id": chunk_id,
                    "content": chunk.page_content,
                    "metadata": metadata,
                    "parent_id": parent_chunk_id,
                }
            )
            if chunk.metadata.get("Header 1"):
                parent_chunk_id = chunk_id

    # Debugging: Print chunks
    print("--- Chunks created ---")
    for chunk in chunks:
        print(f"ID: {chunk['id']}")
        print(f"Content: {chunk['content'][:40]}...")  # Print first 100 chars
        print(f"Metadata: {chunk['metadata']}")
        print("----------------------")
    
    doc_chunks = [chunk["content"] for chunk in chunks]
    embeddings = embedding_model.encode(doc_chunks)
    if len(embeddings) > 0:
        collection.add(
            embeddings=embeddings,
            documents=doc_chunks,
            ids=[chunk["id"] for chunk in chunks],
            metadatas=[chunk["metadata"] for chunk in chunks],
        )

    for chunk in chunks:
        writer.add_document(
            title=chunk["metadata"].get("Header 1", ""),
            content=chunk["content"],
            parent_id=chunk.get("parent_id"),
            id=chunk["id"],
        )
    writer.commit()
    


# --- Constants for Configuration ---
# It's better to manage these in a config file or as function arguments with defaults
SEMANTIC_RESULTS_LIMIT = 10
KEYWORD_RESULTS_LIMIT = 10
RERANK_TOP_K = 3
RRF_K = 60  # Constant for RRF scoring


def _perform_semantic_search(question: str, embedding_model, collection) -> List[str]:
    """Encodes the question and performs a semantic search."""
    question_embedding = embedding_model.encode([question])
    semantic_results = collection.query(
        query_embeddings=question_embedding, n_results=SEMANTIC_RESULTS_LIMIT
    )
    return semantic_results["documents"][0] if semantic_results["documents"] else []


def _perform_keyword_search(question: str, ix) -> List[str]:
    """Performs a keyword search using Whoosh."""
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema, group=syntax.OrGroup).parse(question)
        keyword_results = searcher.search(query, limit=KEYWORD_RESULTS_LIMIT)
        return [res["content"] for res in keyword_results]


def _reciprocal_rank_fusion(
    search_results: List[List[str]], k: int = 60
) -> List[Tuple[str, float]]:
    """
    Performs Reciprocal Rank Fusion on multiple lists of search results.

    Args:
        search_results: A list of lists, where each inner list contains document strings.
        k: A constant used in the RRF formula.

    Returns:
        A list of (document, score) tuples, sorted by score in descending order.
    """
    fused_scores = {}
    # Iterate through each list of search results
    for doc_list in search_results:
        # Iterate through each document in the list with its rank
        for rank, doc in enumerate(doc_list):
            if doc not in fused_scores:
                fused_scores[doc] = 0
            # Add the RRF score for this document from this list
            fused_scores[doc] += 1 / (k + rank + 1)  # rank is 0-indexed

    # Sort the documents by their fused scores in descending order
    reranked_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    return reranked_results


def search_vector_store(question: str) -> str:
    """
    Searches the vector store using an improved hybrid search, fusion, and retrieval strategy.
    """

    expanded_question = _transform_query_with_llm(question)

    # Step 1 & 2: Perform searches (could be run concurrently with asyncio)
    ix = get_whoosh_index()
    semantic_docs = _perform_semantic_search(expanded_question, embedding_model, collection)
    keyword_docs = _perform_keyword_search(expanded_question, ix)

    # Debugging: Print semantic and keyword results
    print("--- Semantic Search Results ---")
    for doc in semantic_docs:
        print(f"  - {doc[:100]}...")
    print("-------------------------------")

    print("--- Keyword Search Results ---")
    for doc in keyword_docs:
        print(f"  - {doc[:100]}...")
    print("------------------------------")

    # Step 3: Fuse results using RRF
    # The RRF function returns a list of (doc, score) tuples. We only need the docs.
    fused_results = _reciprocal_rank_fusion([semantic_docs, keyword_docs], k=RRF_K)
    print("--- Fused Results (top 5) ---")
    for doc, score in fused_results[:5]:
        print(f"  - Score: {score:.4f}, Doc: {doc[:100]}...")
    print("-----------------------------")

    if not fused_results:
        return "No relevant documents found."

    combined_docs = [doc for doc, score in fused_results]

    # Step 4: Rerank the top fused results for final precision
    # Reranking is computationally expensive, so only apply it to the most promising candidates from the fusion step.
    scores = reranker_model.predict(
        [
            (question, doc)
            for doc in combined_docs[: SEMANTIC_RESULTS_LIMIT + KEYWORD_RESULTS_LIMIT]
        ]
    )
    reranked_docs = [doc for _, doc in sorted(zip(scores, combined_docs), reverse=True)]

    # Debugging: Print reranked results
    print("--- Reranked Results (top 5) ---")
    for doc in reranked_docs[:5]:
        print(f"  - {doc[:100]}...")
    print("------------------------------")

    # Step 5: Hierarchical Retrieval (with duplicate prevention)
    final_docs = []
    seen_docs = set()
    with ix.searcher() as searcher:
        for doc_content in reranked_docs[:RERANK_TOP_K]:
            if doc_content not in seen_docs:
                final_docs.append(doc_content)
                seen_docs.add(doc_content)

            # Find the document to get its parent_id
            # Using Term query for exact match is more efficient
            results = searcher.search(Term("content", doc_content), limit=1)
            if results:
                parent_id = results[0].get("parent_id")
                if parent_id:
                    parent_results = searcher.search(Term("id", parent_id), limit=1)
                    if parent_results and parent_results[0]["content"] not in seen_docs:
                        final_docs.append(parent_results[0]["content"])
                        seen_docs.add(parent_results[0]["content"])

    # Debugging: Print final docs
    print("--- Final Docs ---")
    for doc in final_docs:
        print(f"  - {doc}...")
    print("------------------")

    if not final_docs:
        return "No relevant documents found."

    return "\n\n".join(final_docs)

def _transform_query_with_llm(question: str) -> str:
    """
    Uses an LLM to transform the user's question for better retrieval.
    """
    # This "meta-prompt" is crucial for getting good results.
    system_prompt = """You are an expert at rewriting user questions to be more effective for searching a software project's documentation.
    Generate a new query that is a more verbose version of the user's question.
    Include synonyms and related technical terms that would be found in technical documentation.
    For example, if the user asks "how do i make a rescuebox plugin with many operations", a good rewritten query would be "how to create a rescuebox plugin with multiple tasks, operations, commands, or functions".
    Return ONLY the rewritten query.
    """

    try:
        # We can use the same model as the chat component
        response = ollama.chat(
            model="llama3:8b-instruct-q4_K_M",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            # Use low temperature for more predictable query rewriting
            options={"temperature": 0.1},
        )
        expanded_query = response['message']['content'].strip()
        print(f"Expanded query: '{expanded_query}'") # For debugging
        # Fallback to the original question if the LLM returns nothing
        return expanded_query if expanded_query else question
    except Exception as e:
        print(f"LLM query transformation failed: {e}")
        # Fallback to original question on any error
        return question