import argparse

from flask_ml.flask_ml_client import MLClient
from flask_ml.flask_ml_server.models import BatchFileInput, Input

# Define the URL and set up client
IMAGE_MATCH_MODEL_URL = "http://127.0.0.1:5000/findface"
LIST_COLLECTIONS_URL = "http://127.0.0.1:5000/listcollections"
findFaceClient = MLClient(IMAGE_MATCH_MODEL_URL)
listCollectionsClient = MLClient(LIST_COLLECTIONS_URL)


# Set up command line argument parsing
parser = argparse.ArgumentParser(description="To parse text arguments")

# Absolute path of query image
parser.add_argument(
    "--file_paths", metavar="file", type=str, nargs="+", help="Path to images"
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

# Check if collection exists
collections = listCollectionsClient.request({},{})['texts']
collections = [output['value'] for output in collections]

if args.collection_name not in map(lambda c: c.split("_")[0],collections):
    print("Collection does not exist")
    exit()

# Set parameters and inputs for the request
parameters = {
    "similarity_threshold": args.similarity_threshold,
    "collection_name": args.collection_name,
}
inputs = {
    "image_paths": Input(
        root=BatchFileInput.model_validate(
            {"files": [{"path": file_path} for file_path in args.file_paths]}
        )
    )
}

# Response from server
response = findFaceClient.request(inputs, parameters)

# Show results to user

# If reponse is a TextResponse, print the value
if response["output_type"] == "text":
    print(response["value"])

else:
    # Show matches found
    print("\nMatches found")
    for file in response["files"]:
        print(file["path"].split("\\")[-1])
