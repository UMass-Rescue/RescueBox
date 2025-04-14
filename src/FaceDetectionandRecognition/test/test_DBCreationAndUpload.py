import unittest
import chromadb
import pandas as pd
import json

from src.facematch.database_functions import upload_embedding_to_database
from src.facematch.utils.resource_path import get_config_path

class TestUploadEmbeddingToDatabase(unittest.TestCase):
    def setUp(self):
        # Sample data for testing
        self.test_data = [
            {
                "image_path": "test/data/img1.png",
                "embedding": [1, 2, 3],
                "bbox": [1, 2, 300, 200],
                "model_name": 'model',
                "sha256_image": "0",
            },
            {
                "image_path": "test/data/img2.png",
                "embedding": [4, 2, 3],
                "bbox": [5, 2, 300, 200],
                "model_name": 'model',
                "sha256_image": "1",
            },
        ]
        model_config_path = get_config_path("model_config.json")
        with open(model_config_path, "r") as config_file:
            model_config = json.load(config_file)

        self.detector = model_config["detector_backend"].lower()
        self.model_name = model_config["model_name"].lower()

        # DB client
        self.client = chromadb.HttpClient(host="localhost", port=8000)

        # example collection name
        self.collection_name = "sample"


    def test_upload_embedding_to_database(self):
        # Upload data
        upload_embedding_to_database(self.test_data, self.collection_name)
        print(self.model_name)
        # Read data
        result = self.client.get_or_create_collection(f"{self.collection_name}_{self.detector}_{self.model_name}").get(include=["metadatas","embeddings"]) 

        df = pd.DataFrame({"metadatas": result["metadatas"], "embeddings": list(result["embeddings"])})

        # Assert that the header and data are written correctly
        self.assertEqual(df["metadatas"].iloc[0]['image_path'], "test/data/img1.png")
        self.assertEqual(df["embeddings"].iloc[0].tolist(),[1.0,2.0,3.0])

    def test_DB_creation(self):
        # Remove the collection if it exists for the test
        try:
            self.client.delete_collection(f"{self.collection_name}_{self.detector}_{self.model_name}")
        except Exception:
            pass

        upload_embedding_to_database(self.test_data, self.collection_name)

        # Assert that the directory now exists
        self.assertTrue(f"{self.collection_name}_{self.detector}_{self.model_name}" in self.client.list_collections())

    def tearDown(self):
        # Clean up the temporary collection
        try:
            self.client.delete_collection(f"{self.collection_name}_{self.detector}_{self.model_name}")
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
