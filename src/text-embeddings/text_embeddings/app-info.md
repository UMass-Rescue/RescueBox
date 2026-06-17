# Text Search

Text Search performs semantic search over text files. Provide a directory of documents and a search query; if the directory is not yet indexed, it will be embedded automatically, then the most similar documents are returned.

## Inputs

- **Directory:** Path to a directory containing text files to search (.txt, .md, .log).
- **Search Query:** The text to search for. Results are ranked by semantic similarity.

## Parameters

- **Top K Results:** Number of most similar results to return (default: 5).
- **Match threshold:** Similarity score (0–1) above which a result counts as a match. Default 0.5. Scores ~0.12–0.19 are weak; ~0.5+ typically indicates relevance.

## Outputs

- **Search Results:** Each result includes the file path, the matching chunk text, similarity score (0–1), and whether it meets the match threshold. Uses BAAI/bge-small-en-v1.5 with chunk-level search for strong semantic recall (e.g. "stones" matches "pebbles").

### Sample Output

```json
{
  "query": "vehicle collision report",
  "model": "BAAI/bge-m3"",
  "top_k": 5,
  "min_similarity": 0.5,
  "similarity_guidance": "Results with similarity >= 0.5 are marked as matches. Chunk-level search improves recall (e.g. 'stones' matches 'pebbles').",
  "results": [
    {"id": 1, "path": "/evidence/docs/accident.txt", "chunk_index": 0, "similarity": 0.87, "is_match": true, "matching_text": "The vehicle struck the barrier at..."},
    {"id": 2, "path": "/evidence/docs/statement.md", "chunk_index": 1, "similarity": 0.72, "is_match": true, "matching_text": "Witness stated the car was speeding..."}
  ]
}
```

Results can be viewed in the Jobs page. Requires PostgreSQL with pgvector for storing embeddings.

## Pipeline: Image Summary → Text Search

You can chain **Image Summary** with **Text Search** for semantic search over image descriptions. Example prompt: *"Summarize images in /tmp and search for a kid with brown clothes"*.

1. **Image Summary** describes each image and writes `.txt` files to an output directory.
2. **Text Search** receives that directory (and optional file list) and searches for your query using semantic similarity (e.g. "kid" matches "child", "boy", etc.).
