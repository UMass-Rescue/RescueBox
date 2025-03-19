import unittest

from rb_facematch.src.facematch.face_representation import detect_faces_and_get_embeddings
from rb_facematch.src.facematch.utils.resource_path import get_resource_path


class TestApp(unittest.TestCase):

    def test_face_representation(self):
        image_path = get_resource_path("sample_images/single.jpg")
        status, result = detect_faces_and_get_embeddings(
            image_path, "ArcFace", "yolov8"
        )
        assert status is True
        assert len(result[0]["embedding"]) == 512
        assert result[0]["bbox"] == [221, 199, 89, 120]


if __name__ == "__main__":
    unittest.main()
