import argparse
import csv
import os
import pandas as pd
import numpy as np
import time
from dotenv import load_dotenv
import ast
import json

# from flask_ml.flask_ml_client import MLClient
from rb.api.models import ResponseBody
from fastapi.testclient import TestClient
from rb.api.main import app


def query_find_face_bulk(query_directory, collection_name):
    # Define the URL and set up client
    # IMAGE_MATCH_MODEL_URL = "http://127.0.0.1:5000/findfacebulktesting"
    # LIST_COLLECTIONS_URL = "http://127.0.0.1:5000/listcollections"
    # findFaceClient = MLClient(IMAGE_MATCH_MODEL_URL)
    # listCollectionsClient = MLClient(LIST_COLLECTIONS_URL)

    client = TestClient(app)

    # Check if collection exists
    response = client.post(
        "/face-match/listcollections", json={"inputs": {}, "parameters": {}}
    )
    body = ResponseBody(**response.json())
    collections = [text.value for text in body.root.texts]

    if collection_name not in map(lambda c: c.split("_")[0], collections):
        print("Collection does not exist")
        exit()

    # Set parameters and inputs for the request
    parameters = {
        "collection_name": collection_name,
    }

    absolute_query_directory = os.path.abspath(query_directory)

    inputs = {"query_directory": {"path": str(absolute_query_directory)}}

    # Input(
    #         root=DirectoryInput.model_validate({"path": absolute_query_directory})
    #     )

    input_data = {
        "inputs": inputs,
        "parameters": parameters,
    }

    # Response from server
    response = client.post("/face-match/findfacebulktesting", json=input_data)
    try:
        body = ResponseBody(**response.json())
        response_data = ast.literal_eval(body.root.value)
        return response_data

    except Exception:
        # If response is not an array, print the value
        print(response["value"])
        return response["value"]


load_dotenv()

# Set up command line argument parsing
parser = argparse.ArgumentParser(description="To parse text arguments")

# Absolute path of query image
parser.add_argument(
    "--query_directory",
    required=True,
    metavar="directory",
    type=str,
    help="Path to images",
)

# Name of embedding collection from user
parser.add_argument(
    "--collection_name", required=True, type=str, help="Name of the collection file"
)

# benchmark results path
parser.add_argument(
    "--results_path",
    required=False,
    type=str,
    help="Parent Results directory",
    default=".",
)

# results_name
parser.add_argument(
    "--results_name",
    required=False,
    type=str,
    help="Name of results output",
    default="results",
)

args = parser.parse_args()

similarity_thresholds = (round(st, 2) for st in np.arange(0.40, 0.80, 0.02))

module_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(module_dir, os.pardir))
FACEMATCH_DIR = os.path.join(project_root, "face_detection_recognition")
model_config_path = os.path.join(FACEMATCH_DIR, "config", "model_config.json")
with open(model_config_path, "r") as config_file:
    config = json.load(config_file)
model_name = config["model_name"]
detector_backend = config["detector_backend"]


# Bulk query and measure time
start_time = time.time()
results = query_find_face_bulk(args.query_directory, args.collection_name)
end_time = time.time()

elapsed_time = end_time - start_time
print(f"Time taken for face find bulk: {elapsed_time}")

abs_results_path = os.path.join(
    os.getcwd(),
    "src",
    "face-detection-recognition",
    "benchmark_testing",
    "benchmark-results",
    f"{detector_backend}-{model_name}-{args.results_name}",
)

times_csv_path = os.path.join(
    abs_results_path,
    "times.csv",
)

with open(times_csv_path, "a", newline="") as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["bulk_face_find", elapsed_time])

for st in similarity_thresholds:
    query_results = results.values()
    data = []
    for query_idx, query_result in enumerate(results.items()):
        for face_idx, face in enumerate(query_result[1]):
            data.append(
                {
                    "similarity": face["similarity"],
                    "query_idx": query_idx,
                    "face_idx": face["face_idx"],
                    "img_path": face["img_path"],
                }
            )

    df = pd.DataFrame(data)
    # sort results by similarity in descending order
    df = df.sort_values(
        by=["query_idx", "face_idx", "similarity"], ascending=[True, True, False]
    )

    # Function to filter paths based on similarity threshold, but keep an empty list if none qualify
    def filter_by_similarity(group):
        paths = group.loc[group["similarity"] >= st, "img_path"].tolist()
        return paths if paths else []

    top_img_paths = (
        df.groupby("query_idx", sort=False, group_keys=False)
        .apply(filter_by_similarity, include_groups=False)
        .tolist()
    )

    output_csv_path = os.path.join(
        abs_results_path,
        "output-csv-dump",
        f"{detector_backend}_{model_name}_{st}.csv",
    )
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    with open(output_csv_path, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["filename", "result"])

        for query_path, match_paths in zip(results.keys(), top_img_paths):
            query_name = os.path.basename(query_path)
            match_paths = " ".join(
                list(map(lambda path: os.path.basename(path), match_paths))
            )

            csvwriter.writerow([query_name, match_paths])
