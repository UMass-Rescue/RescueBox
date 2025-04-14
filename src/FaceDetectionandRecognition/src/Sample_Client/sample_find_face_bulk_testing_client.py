import argparse
import os
import time
from dotenv import load_dotenv
import ast
import pandas as pd

from flask_ml.flask_ml_client import MLClient
from flask_ml.flask_ml_server.models import DirectoryInput, Input

load_dotenv()

# Set up command line argument parsing
parser = argparse.ArgumentParser(description="To parse text arguments")

# Absolute path of query image
parser.add_argument(
    "--query_directory", required=True, metavar="directory", type=str, help="Path to images"
)

# Name of embedding collection from user
parser.add_argument(
    "--collection_name", required=True, type=str, help="Name of the collection file"
)

# Face Similarity threshold from user
parser.add_argument(
    "--similarity_threshold",
    type=float,
    help="Return matches with similarity above this threshold",
)

args = parser.parse_args()

# Define the URL and set up client
IMAGE_MATCH_MODEL_URL = "http://127.0.0.1:5000/findfacebulktesting"
LIST_COLLECTIONS_URL = "http://127.0.0.1:5000/listcollections"
findFaceClient = MLClient(IMAGE_MATCH_MODEL_URL)
listCollectionsClient = MLClient(LIST_COLLECTIONS_URL)


# Check if collection exists
collections = listCollectionsClient.request({},{})['texts']
collections = [output['value'] for output in collections]

if args.collection_name not in map(lambda c: c.split("_")[0],collections):
    print("Collection does not exist")
    exit()

# Set parameters and inputs for the request
parameters = {
    "collection_name": args.collection_name,
}

absolute_query_directory = os.path.abspath(args.query_directory)

inputs = {
    "query_directory": Input(
        root=DirectoryInput.model_validate(
            {
                "path": absolute_query_directory
            }
        )
    )
}

# Response from server
start_time = time.time()
response = findFaceClient.request(inputs, parameters)
try:
    results = ast.literal_eval(response['value'])
    query_results = results.values()
    data = []
    for query_idx, query_result in enumerate(results.items()):
        for face_idx, face in enumerate(query_result[1]):
            data.append({
                'similarity': face['similarity'],
                'query_idx': query_idx,
                'face_idx': face['face_idx'],
                'img_path': face['img_path']
            })

    df = pd.DataFrame(data)
    # sort results by similarity in descending order
    df = df.sort_values(by=["query_idx", "face_idx", "similarity"], ascending=[True, True, False])

    # Function to filter paths based on similarity threshold, but keep an empty list if none qualify
    def filter_by_similarity(group):
        paths = group.loc[group['similarity'] >= 0.5, 'img_path'].tolist()
        return paths if paths else []
    
    top_img_paths = df.groupby('query_idx', sort=False).apply(filter_by_similarity).tolist()

    for query_path, match_paths in zip(results.keys(), top_img_paths):
        query_name = os.path.basename(query_path)
        match_paths = " ".join(list(map(lambda path: os.path.basename(path),match_paths)))
        print(f"Query: {query_name}    Matches: {match_paths}")

except Exception:
    # If response is not an array, print the value
    print(response["value"])




end_time = time.time()

elapsed_time = end_time - start_time
print(f"Time taken for face find bulk: {elapsed_time}")