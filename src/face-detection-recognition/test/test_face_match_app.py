from rb.lib.common_tests import RBAppTest
from face_detection_recognition import face_match_server as fm_server
from rb.api.models import AppMetadata


class TestFaceMatch(RBAppTest):
    def setup_method(self):
        self.set_app(fm_server.app, fm_server.APP_NAME)

    def get_metadata(self):
        return AppMetadata(
            name="Face Recognition and Matching",
            plugin_name=fm_server.APP_NAME,
            author="FaceMatch Team",
            version="0.1.0",
            info=fm_server.info,
        )

    def get_all_ml_services(self):
        return [
            (
                0,
                "findface",
                "Find Face",
                fm_server.get_ingest_query_image_task_schema(),
            ),
            (
                1,
                "findfacebulk",
                "Face Find Bulk",
                fm_server.get_ingest_bulk_query_image_task_schema(),
            ),
            (
                2,
                "findfacebulktesting",
                "Face Find Bulk Test",
                fm_server.get_ingest_bulk_test_query_image_task_schema(),
            ),
            (3, "bulkupload", "Bulk Upload", fm_server.get_ingest_images_task_schema()),
            (
                4,
                "deletecollection",
                "Delete Collection",
                fm_server.delete_collection_task_schema(),
            ),
            (
                5,
                "listcollections",
                "List Collection",
                fm_server.list_collections_task_schema(),
            ),
        ]
