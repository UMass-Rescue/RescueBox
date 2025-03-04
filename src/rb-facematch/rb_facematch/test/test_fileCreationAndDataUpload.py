import os
import unittest

import faiss
import pandas as pd

from rb_facematch.src.facematch.database_functions import upload_embedding_to_database


class TestUploadEmbeddingToDatabase(unittest.TestCase):
    def setUp(self):
        # Sample data for testing
        self.test_data = [
            {
                "image_path": "test/data/img1.png",
                "embedding": [1, 2, 3],
                "bbox": [1, 2, 300, 200],
            },
            {
                "image_path": "test/data/img2.png",
                "embedding": [4, 2, 3],
                "bbox": [5, 2, 300, 200],
            },
        ]

        # Database file
        self.csv_file = "test/data/test_embeddings.csv"

        # Construct the Faiss index path
        self.faiss_path = self.csv_file.replace(".csv", ".bin")

    def test_upload_embedding_to_database(self):
        # Upload data
        upload_embedding_to_database(self.test_data, self.csv_file)

        # Read data
        df = pd.read_csv(self.csv_file)

        # Assert that the header and data are written correctly
        self.assertEqual(df.iloc[0, 0], "test/data/img1.png")
        self.assertEqual(df.iloc[0, 1], "1,2,3")
        self.assertEqual(df.iloc[0, 2], "1,2,300,200")

    def test_faiss_index(self):
        # Upload data
        upload_embedding_to_database(self.test_data, self.csv_file)

        # Assert that the Faiss index file was created
        assert os.path.exists(self.faiss_path)

        # Load the Faiss index and check the number of embeddings
        index = faiss.read_index(self.faiss_path)

        assert index.ntotal == len(self.test_data)

    def test_directory_creation(self):
        # Remove the directory if it exists for the test
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)

        upload_embedding_to_database(self.test_data, self.csv_file)

        # Assert that the directory now exists
        self.assertTrue(os.path.exists(self.csv_file))

    def tearDown(self):
        # Clean up the temporary CSV file
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)

        # Clean up the temporary FAISS file
        if os.path.exists(self.faiss_path):
            os.remove(self.faiss_path)


if __name__ == "__main__":
    unittest.main()
