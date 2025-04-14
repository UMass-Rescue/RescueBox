import argparse
from dotenv import load_dotenv

from flask_ml.flask_ml_client import MLClient
from flask_ml.flask_ml_server.models import TextInput, Input

load_dotenv()

# Set up command line argument parsing
parser = argparse.ArgumentParser(description="To parse text arguments")

# Name of embedding collection from user
parser.add_argument(
    "--collection_name", required=True, type=str, help="Name of the collection"
)

# Name of embedding collection from user
parser.add_argument(
    "--model_name", required=True, type=str, help="Name of the embedding model"
)

# Name of embedding collection from user
parser.add_argument(
    "--detector_backend", required=True, type=str, help="Name of the detector model"
)

args = parser.parse_args()

# Define the URL and set up client
IMAGE_MATCH_MODEL_URL = "http://127.0.0.1:5000/deletecollection"
client = MLClient(IMAGE_MATCH_MODEL_URL)


inputs = {
    "collection_name": Input(
        root=TextInput.model_validate(
            {
                "text": args.collection_name
            }
        )
    ),
    "model_name": Input(
        root=TextInput.model_validate(
            {
                "text": args.model_name
            }
        )
    ),
    "detector_backend": Input(
        root=TextInput.model_validate(
            {
                "text": args.detector_backend
            }
        )
    ),
}

# Response from server
response = client.request(inputs, {})
print(response)
print(response["value"])