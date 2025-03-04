import os

import faiss
import numpy as np


def add_embeddings_faiss_index(embeddings, database_filepath):
    """
    This function will add new embeddings to the faiss index and save the index.
    """
    # Create a new path with the ".bin" extension
    faiss_path = database_filepath.replace(".csv", ".bin")

    # Normalize the embeddings
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings.astype("float32")

    if not os.path.exists(faiss_path):
        os.makedirs(os.path.dirname(faiss_path), exist_ok=True)
        # Create faiss index
        index = faiss.IndexFlatIP(embeddings.shape[1])
    else:
        # Load the faiss index
        index = faiss.read_index(faiss_path)

    # Add the new embeddings
    index.add(embeddings)

    # Save Faiss index to disk
    faiss.write_index(index, faiss_path)
