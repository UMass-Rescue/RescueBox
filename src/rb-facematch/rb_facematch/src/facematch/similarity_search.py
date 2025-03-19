import logging
import faiss
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
pd.options.mode.chained_assignment = None  # default='warn'


def cosine_similarity_search(query_vector, database_filepath, top_n=5, threshold=None):
    csv_file = database_filepath

    # Read the CSV file into a DataFrame and Embeddings stored as str to lists
    df = pd.read_csv(csv_file)
    df["embedding"] = df["embedding"].apply(lambda x: list(map(float, x.split(","))))

    # Compute cosine similarity between the query vector and each vector in the 'embedding' column
    df["similarity"] = df["embedding"].apply(
        lambda x: cosine_similarity([x], [query_vector])[0][0]
    )

    # Get top n based on similarity in descending order
    results = df.nlargest(top_n, "similarity")

    logger.debug(results[["image_path", "embedding", "similarity"]])

    if threshold is not None:
        # Filter the DataFrame based on the threshold
        results = results[results["similarity"] >= threshold]

    # Return the image paths corresponding to the top N similar vectors or vectors with similarity higher than threshold
    top_img_paths = results["image_path"].to_list()

    return top_img_paths


def cosine_similarity_search_faiss(
    query_vector, database_filepath, top_n=5, threshold=None
):
    # Normalize the query vector
    query_vector = query_vector / np.linalg.norm(query_vector)
    query_vector = query_vector.astype("float32")
    faiss_path = database_filepath.replace(".csv", ".bin")

    # Load the faiss index
    index = faiss.read_index(faiss_path)

    distances, indices = index.search(query_vector.reshape(1, -1), top_n)
    indices = indices[0]
    indices = indices.tolist()

    df = pd.read_csv(database_filepath)

    results = df.iloc[[i for i in indices if i != -1]]

    results["embedding"] = results["embedding"].apply(
        lambda x: list(map(float, x.split(",")))
    )

    results["similarity"] = results["embedding"].apply(
        lambda x: cosine_similarity([x], [query_vector])[0][0]
    )

    logger.debug(results[["image_path", "embedding", "similarity"]])

    if threshold is not None:
        # Filter the DataFrame based on the threshold
        results = results[results["similarity"] >= threshold]

    # Return the image paths corresponding to the top N similar vectors or vectors with similarity higher than threshold
    top_img_paths = results["image_path"].to_list()

    return top_img_paths


def euclidean_distance_search_faiss(
    query_vector, database_filepath, top_n=None, threshold=None
):
    # Ensure at least one of top_n or threshold is set
    if top_n is None and threshold is None:
        raise ValueError("Either top_n or threshold must be specified.")

    # Normalize the query vector
    query_vector = np.array(query_vector).reshape(1, -1).astype("float32")

    faiss_path = database_filepath.replace(".csv", ".bin")

    # Load the faiss index
    index = faiss.read_index(faiss_path)

    if top_n:
        distances, indices = index.search(query_vector, top_n)
        indices = indices[0][indices[0] != -1]
    else:
        # Perform a Range Search
        radius = threshold  # adjust this value to control the search radius
        lims, distances, indices = index.range_search(query_vector, radius)

        start = lims[0]
        end = lims[1]
        indices = indices[start:end]

    df = pd.read_csv(database_filepath)

    top_img_paths = [df["image_path"].iloc[i] for i in indices]

    return top_img_paths
