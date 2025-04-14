import argparse

from flask_ml.flask_ml_client import MLClient
from flask_ml.flask_ml_server.models import BatchDirectoryInput, Input

# Define the URL and set up client
BULK_UPLOAD_MODEL_URL = "http://127.0.0.1:5000/bulkupload"
bulkUploadClient = MLClient(BULK_UPLOAD_MODEL_URL)
LIST_COLLECTIONS_URL = "http://127.0.0.1:5000/listcollections"
listCollectionsClient = MLClient(LIST_COLLECTIONS_URL)

# Set up command line argument parsing
parser = argparse.ArgumentParser(description="To parse text arguments")

# Absolute path of directory of images
parser.add_argument(
    "--directory_paths",
    metavar="file",
    type=str,
    nargs="+",
    help="Path to directory containing images",
)

# Name of embedding collection from user
parser.add_argument(
    "--collection_name", required=True, type=str, help="Name of the embedding collection"
)

args = parser.parse_args()

# Dropdown collection path is used to give the option of creating a new collection and selecting an existing collection for users in frontend
# Set dropdown collection path to the name of the collection if it exists, otherwise set it to "Create a new collection"
collections_response = listCollectionsClient.request({},{})
collections = [output['value'] for output in collections_response['texts']]

if args.collection_name in map(lambda c: c.split("_")[0],collections):
    dropdown_collection_name = args.collection_name
else:
    dropdown_collection_name = "Create a new collection"

# Set parameters and inputs for the request
parameters = {
    "collection_name": args.collection_name,
    "dropdown_collection_name": dropdown_collection_name,
}
inputs = {
    "directory_paths": Input(
        root=BatchDirectoryInput.model_validate(
            {
                "directories": [
                    {"path": directory_path} for directory_path in args.directory_paths
                ]
            }
        )
    ) 
}

# Response from the server
response = bulkUploadClient.request(inputs, parameters)
print("Bulk Upload model response")
print(response, "\n")
