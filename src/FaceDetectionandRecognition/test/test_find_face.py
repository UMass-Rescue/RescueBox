import os
import unittest
import chromadb
import json

from src.facematch.interface import FaceMatchModel
from src.facematch.utils.resource_path import (get_config_path, get_resource_path)


class TestMatchFace(unittest.TestCase):

    def setUp(self):
        self.image_directory_path = get_resource_path("sample_db")
        self.collection_name = "sample"
        self.image_file_path = get_resource_path("test_image.jpg")
        self.client = chromadb.HttpClient(host='localhost', port=8000)
        
        # get model name in order to determine full collection name
        config_path = get_config_path("model_config.json")
        with open(config_path, "r") as config_file:
            config = json.load(config_file)
        self.model_name = config["model_name"]
        
    def test_match_face_success(self):
        face_match_object = FaceMatchModel()
        face_match_object.bulk_upload(self.image_directory_path, self.collection_name)
        status, matching_images = face_match_object.find_face(
            self.image_file_path, threshold=None, collection_name=self.collection_name
        )
        self.assertTrue("Bill_Belichick_0002.jpg" in list(map(lambda x: os.path.basename(x), matching_images)))

    def tearDown(self):
        try:
            self.client.delete_collection(f"{self.collection_name}_{self.model_name.lower()}")
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()
