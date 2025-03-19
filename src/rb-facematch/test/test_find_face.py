import os
import unittest

from rb_facematch.src.facematch.interface import FaceMatchModel
from rb_facematch.src.facematch.utils.resource_path import get_resource_path


class TestMatchFace(unittest.TestCase):

    def setUp(self):
        self.image_directory_path = get_resource_path("sample_images")
        self.database_path = get_resource_path("test_db.csv")
        self.image_file_path = get_resource_path("test_image.jpg")
        self.faiss_database_path = get_resource_path("test_db.bin")

    def test_match_face_success(self):
        face_match_object = FaceMatchModel()
        face_match_object.bulk_upload(self.image_directory_path, self.database_path)
        status, matching_images = face_match_object.find_face(
            self.image_file_path, threshold=None, database_path=self.database_path
        )
        self.assertEqual(1, len(matching_images))
        self.assertEqual("many.jpg", os.path.basename(matching_images[0]))

    def tearDown(self):
        if os.path.exists(self.database_path):
            os.remove(self.database_path)

        if os.path.exists(self.faiss_database_path):
            os.remove(self.faiss_database_path)


if __name__ == "__main__":
    unittest.main()
