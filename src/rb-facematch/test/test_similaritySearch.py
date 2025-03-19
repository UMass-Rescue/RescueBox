import os
import unittest

import pandas as pd

from rb_facematch.src.facematch.database_functions import upload_embedding_to_database
from rb_facematch.src.facematch.similarity_search import (cosine_similarity_search,
                                             cosine_similarity_search_faiss)


class TestCosineSimilarity(unittest.TestCase):
    def setUp(self):
        # Create a temporary CSV file for testing
        self.csv_file = "test/data/test_embeddings.csv"
        test_data = [
            {
                "image_path": "test/data/img1.png",
                "embedding": [1, 2, 3],
                "bbox": (1, 2, 300, 200),
            },
            {
                "image_path": "test/data/img2.png",
                "embedding": [4, 2, 3],
                "bbox": (5, 2, 300, 200),
            },
        ]
        # Convert Embeddings to lists to store in CSV
        df = pd.DataFrame(test_data)
        df["embedding"] = df["embedding"].apply(lambda x: ",".join(map(str, x)))
        df.to_csv(self.csv_file, index=False)

        # Example query vector
        self.query_vector = [0.1, 0.2, 0.3]

    def test_cosine_similarity_top_n(self):
        # Test with top_n parameter
        top_img_paths = cosine_similarity_search(
            self.query_vector, self.csv_file, top_n=2
        )

        # Assert that the top 2 image paths are returned
        self.assertEqual(len(top_img_paths), 2)
        self.assertIn("test/data/img1.png", top_img_paths)

    def test_cosine_similarity_threshold(self):
        # Test with threshold parameter
        top_img_paths = cosine_similarity_search(
            self.query_vector, self.csv_file, threshold=0.95
        )

        # Assert that the correct image paths are returned based on the threshold
        self.assertTrue(len(top_img_paths) >= 1)
        self.assertIn("test/data/img1.png", top_img_paths)

    def tearDown(self):
        # Clean up the temporary CSV file
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)


class TestCosineSimilarityFAISS(unittest.TestCase):
    def setUp(self):
        # Create a temporary CSV file for testing
        self.csv_file = "test/data/test_embeddings.csv"
        self.faiss_path = "test/data/test_embeddings.bin"
        test_data = [
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
        # Upload embeddings to database
        upload_embedding_to_database(test_data, self.csv_file)

        # Example query vector
        self.query_vector = [0.1, 0.2, 0.3]

    def test_cosine_similarity_top_n(self):
        # Test with top_n parameter
        top_img_paths = cosine_similarity_search_faiss(
            self.query_vector, self.csv_file, top_n=2
        )

        # Assert that the top 2 image paths are returned
        self.assertEqual(len(top_img_paths), 2)
        self.assertIn("test/data/img1.png", top_img_paths)

    def test_cosine_similarity_threshold(self):
        # Test with threshold parameter
        top_img_paths = cosine_similarity_search_faiss(
            self.query_vector, self.csv_file, threshold=0.68
        )

        # Assert that the correct image paths are returned based on the threshold
        self.assertTrue(len(top_img_paths) >= 1)
        self.assertIn("test/data/img1.png", top_img_paths)

    def tearDown(self):
        # Clean up the temporary CSV file
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)

        # Clean up the temporary FAISS file
        if os.path.exists(self.faiss_path):
            os.remove(self.faiss_path)


if __name__ == "__main__":
    unittest.main()
