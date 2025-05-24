import os
import uuid
import unittest
from pathlib import Path
import pytest
import sys
import onnxruntime

from face_detection_recognition.face_match_server import (
    app as cli_app,
    APP_NAME,
    server,
    DB,
)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

# Force CPU execution for testing - ONNX Runtime settings
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["ONNX_DEVICE"] = "CPU"

try:
    original_get_available_providers = onnxruntime.get_available_providers
    onnxruntime.get_available_providers = lambda: ["CPUExecutionProvider"]
    # Set global ONNX session options to prefer CPU
    onnxruntime.set_default_logger_severity(3)
    print("Successfully configured ONNX Runtime for CPU-only execution")
except ImportError:
    print("ONNX Runtime issue")

try:
    from rb.api.models import (
        ResponseBody,
        TextResponse,
        # BatchTextResponse,
        # BatchFileResponse,
    )
    from rb.lib.common_tests import RBAppTest

    rb_imported = True
except ImportError:
    print("Failed to import rb modules. Attempting a different approach...")
    rb_imported = False


TEST_IMAGES_DIR = Path("src/face-detection-recognition/resources/sample_db")
TEST_FACES_DIR = Path(
    "src/face-detection-recognition/resources/sample_queries"
)  # Directory with clear face images
TEST_QUERY_IMAGE = TEST_FACES_DIR / "Bill_Belichick_0002.jpg"
TEST_MODEL_NAME = "facenet512"  # Default model
TEST_DETECTOR_BACKEND = "retinaface"  # Default detector


class TestFaceMatch(RBAppTest):
    has_test_images = os.path.exists(TEST_QUERY_IMAGE)
    print(TEST_QUERY_IMAGE.absolute())

    @classmethod
    def setup_class(cls):
        """Set up the test environment once before all test methods"""

        os.makedirs(TEST_IMAGES_DIR, exist_ok=True)
        os.makedirs(TEST_FACES_DIR, exist_ok=True)

        # Generate a unique test collection name
        cls.test_collection_name = f"test_collection_{uuid.uuid4().hex[:8]}"
        cls.full_collection_name = f"{cls.test_collection_name}_{TEST_DETECTOR_BACKEND[0:2].lower()}{TEST_MODEL_NAME[0:2].lower()}S"

        print("=" * 80)
        print("Test setup complete. Using CPU mode for testing with ONNX Runtime.")
        print(f"Test images available: {cls.has_test_images}")
        print(f"Testing with collection: {cls.test_collection_name}")
        print("=" * 80)

    @classmethod
    def teardown_class(cls):
        """Clean up after all tests"""
        # Delete our test collection if it exists
        try:
            if hasattr(cls, "full_collection_name"):
                collections = DB.client.list_collections()
                collection_names = [col.name for col in collections]
                if cls.full_collection_name in collection_names:
                    DB.client.delete_collection(cls.full_collection_name)
                    print(f"Deleted test collection: {cls.full_collection_name}")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

    def setup_method(self):
        """Set up before each test method"""
        self.set_app(cli_app, APP_NAME)

    def get_metadata(self):
        """Return app metadata for testing"""
        return server._app_metadata

    def get_all_ml_services(self):
        """Return all ML services for testing"""
        from face_detection_recognition.face_match_server import (
            # get_ingest_query_image_task_schema,
            get_ingest_bulk_query_image_task_schema,
            # get_ingest_bulk_test_query_image_task_schema,
            get_ingest_images_task_schema,
            delete_collection_task_schema,
            # list_collections_task_schema,
            # get_multi_pipeline_face_find_bulk_task_schema,
            # get_multi_pipeline_ingest_images_task_schema,
        )

        return [
            # (0, "findface", "Find Face", get_ingest_query_image_task_schema()),
            (
                1,
                "findfacebulk",
                "Face Find Bulk",
                get_ingest_bulk_query_image_task_schema(),
            ),
            # (
            #     2,
            #     "findfacebulktesting",
            #     "Face Find Bulk Test",
            #     get_ingest_bulk_test_query_image_task_schema(),
            # ),
            (3, "bulkupload", "Bulk Upload", get_ingest_images_task_schema()),
            # (
            #     6,
            #     "multi_pipeline_bulkupload",
            #     "Multi-Pipeline Bulk Upload",
            #     get_multi_pipeline_ingest_images_task_schema()
            # ),
            # (
            #     7,
            #     "multi_pipeline_findfacebulk",
            #     "Multi-Pipeline Find Face Bulk",
            #     get_multi_pipeline_face_find_bulk_task_schema()
            # ),
            (
                4,
                "deletecollection",
                "Delete Collection",
                delete_collection_task_schema(),
            ),
            # (5, "listcollections", "List Collection", list_collections_task_schema()),
        ]

    def get_expected_routes(self):
        """Return expected routes for testing, matching actual server implementation"""
        return [
            # {
            #     "task_schema": f"/{APP_NAME}/findface/task_schema",
            #     "run_task": f"/{APP_NAME}/findface",
            #     "short_title": "Find Face",
            #     "order": 0,
            # },
            {
                "task_schema": f"/{APP_NAME}/findfacebulk/task_schema",
                "run_task": f"/{APP_NAME}/findfacebulk",
                "short_title": "Face Find Bulk",
                "order": 1,
            },
            # {
            #     "task_schema": f"/{APP_NAME}/findfacebulktesting/task_schema",
            #     "run_task": f"/{APP_NAME}/findfacebulktesting",
            #     "short_title": "Face Find Bulk Test",
            #     "order": 2,
            # },
            {
                "task_schema": f"/{APP_NAME}/bulkupload/task_schema",
                "run_task": f"/{APP_NAME}/bulkupload",
                "short_title": "Bulk Upload",
                "order": 0,
            },
            # {
            #     "task_schema": f"/{APP_NAME}/multi_pipeline_bulkupload/task_schema",
            #     "run_task": f"/{APP_NAME}/multi_pipeline_bulkupload",
            #     "short_title": "Multi-Pipeline Bulk Upload",
            #     "order": 6
            # },
            # {
            #     "task_schema": f"/{APP_NAME}/multi_pipeline_findfacebulk/task_schema",
            #     "run_task":  f"/{APP_NAME}/multi_pipeline_findfacebulk",
            #     "short_title": "Multi-Pipeline Find Face Bulk",
            #     "order": 7,
            # },
            {
                "task_schema": f"/{APP_NAME}/deletecollection/task_schema",
                "run_task": f"/{APP_NAME}/deletecollection",
                "short_title": "Delete Collection",
                "order": 2,
            },
            # {
            #     "task_schema": f"/{APP_NAME}/listcollections/task_schema",
            #     "run_task": f"/{APP_NAME}/listcollections",
            #     "short_title": "List Collection",
            #     "order": 5,
            # },
        ]

    def test_01_metadata_and_schemas(self):
        """Test app metadata and task schemas"""
        # Check app metadata
        metadata = self.get_metadata()
        assert metadata.name == "Face Recognition and Matching"
        assert metadata.plugin_name == APP_NAME
        assert metadata.author == "FaceMatch Team"

        # Check task schemas
        from face_detection_recognition.face_match_server import (
            get_ingest_query_image_task_schema,
            get_ingest_bulk_query_image_task_schema,
            get_ingest_images_task_schema,
            delete_collection_task_schema,
            get_multi_pipeline_face_find_bulk_task_schema,
            get_multi_pipeline_ingest_images_task_schema,
            list_collections_task_schema,
        )

        # Test that each schema returns a valid TaskSchema object
        schemas = [
            get_ingest_query_image_task_schema(),
            get_ingest_bulk_query_image_task_schema(),
            get_ingest_images_task_schema(),
            get_multi_pipeline_face_find_bulk_task_schema(),
            get_multi_pipeline_ingest_images_task_schema(),
            delete_collection_task_schema(),
            list_collections_task_schema(),
        ]

        for schema in schemas:
            assert schema is not None
            assert hasattr(schema, "inputs")

    def test_02_config_loading(self):
        """Test that config file exists and can be loaded"""
        from face_detection_recognition.face_match_server import config, config_path

        assert os.path.exists(config_path), "Config file not found"
        assert "cosine-threshold" in config, "Config missing cosine-threshold key"
        assert isinstance(
            config["cosine-threshold"], (int, float)
        ), "Threshold not numeric"

    # def test_03_list_collections_endpoint(self):
    #     """Test the list_collections endpoint"""

    #     list_collection_api = f"/{APP_NAME}/listcollections"

    #     response = self.client.post(
    #         list_collection_api, json={"inputs": {}, "parameters": {}}
    #     )

    #     assert response.status_code == 200
    #     body = ResponseBody(**response.json())
    #     assert isinstance(body.root, BatchTextResponse)
    #     # Store collections for later comparison
    #     self.initial_collections = [text.value for text in body.root.texts]
    #     print(f"Initial collections: {self.initial_collections}")

    @pytest.mark.skipif(not has_test_images, reason="Test images not available")
    def test_04_bulk_upload_endpoint(self):
        """Test the bulk_upload endpoint to create our test collection"""

        bulk_upload_api = f"/{APP_NAME}/bulkupload"
        input_data = {
            "inputs": {"directory_path": {"path": str(TEST_IMAGES_DIR)}},
            "parameters": {
                "dropdown_collection_name": "Create a new collection",
                "collection_name": self.__class__.test_collection_name,
            },
        }
        response = self.client.post(bulk_upload_api, json=input_data)

        assert response.status_code == 200
        body = ResponseBody(**response.json())
        assert isinstance(body.root, TextResponse)
        # Check if the response contains a success message
        result_text = body.root.value
        print(f"Bulk upload result: {result_text}")
        assert "Successfully uploaded" in result_text or "No faces" in result_text

        # If successful, verify the collection exists
        if "Successfully uploaded" in result_text and "0 faces" not in result_text:
            collections = DB.client.list_collections()
            collection_names = [col.name for col in collections]
            print(collection_names)
            assert (
                self.__class__.full_collection_name in collection_names
            ), "Collection was not created"
            print(f"Created collection: {self.__class__.full_collection_name}")

    # @pytest.mark.skipif(not has_test_images, reason="Test images not available")
    # def test_05_find_face_endpoint(self):
    #     """Test the find_face endpoint with our test collection"""
    #     # Make sure we have a collection
    #     collections = DB.client.list_collections()
    #     collection_names = [col.name for col in collections]
    #     if self.__class__.full_collection_name not in collection_names:
    #         pytest.skip(
    #             f"Test collection {self.__class__.full_collection_name} not available"
    #         )

    #     find_face_api = f"/{APP_NAME}/findface"
    #     input_data = {
    #         "inputs": {"image_paths": {"files": [{"path": str(TEST_QUERY_IMAGE)}]}},
    #         "parameters": {
    #             "collection_name": self.__class__.test_collection_name,
    #             "similarity_threshold": 0.5,
    #         },
    #     }

    #     response = self.client.post(find_face_api, json=input_data)

    #     assert response.status_code == 200
    #     body = ResponseBody(**response.json())
    #     # The response could be TextResponse (no matches) or BatchFileResponse (matches found)
    #     assert isinstance(body.root, (TextResponse, BatchFileResponse))

    #     if isinstance(body.root, TextResponse):
    #         print(f"Find face result (text): {body.root.value}")
    #     else:
    #         print(f"Find face result (files): {len(body.root.files)} matches found")

    @pytest.mark.skipif(not has_test_images, reason="Test images not available")
    def test_06_find_face_bulk_endpoint(self):
        """Test the find_face_bulk endpoint with our test collection"""
        # Make sure we have a collection
        collections = DB.client.list_collections()
        collection_names = [col.name for col in collections]
        if self.__class__.full_collection_name not in collection_names:
            pytest.skip(
                f"Test collection {self.__class__.full_collection_name} not available"
            )

        find_face_bulk_api = f"/{APP_NAME}/findfacebulk"
        input_data = {
            "inputs": {"query_directory": {"path": str(TEST_FACES_DIR)}},
            "parameters": {
                "collection_name": self.__class__.test_collection_name,
                "similarity_threshold": 0.5,
            },
        }

        # Send the request
        response = self.client.post(find_face_bulk_api, json=input_data)

        # Assert response
        assert response.status_code == 200
        body = ResponseBody(**response.json())
        assert isinstance(body.root, TextResponse)
        print(f"Find face bulk result: {body.root.value}...")

    # @pytest.mark.skipif(not has_test_images, reason="Test images not available")
    # def test_07_find_face_bulk_testing_endpoint(self):
    #     """Test the find_face_bulk_testing endpoint with our test collection"""
    #     # Make sure we have a collection
    #     collections = DB.client.list_collections()
    #     collection_names = [col.name for col in collections]
    #     if self.__class__.full_collection_name not in collection_names:
    #         pytest.skip(
    #             f"Test collection {self.__class__.full_collection_name} not available"
    #         )

    #     find_face_bulk_testing_api = f"/{APP_NAME}/findfacebulktesting"
    #     input_data = {
    #         "inputs": {"query_directory": {"path": str(TEST_FACES_DIR)}},
    #         "parameters": {"collection_name": self.__class__.test_collection_name},
    #     }

    #     response = self.client.post(find_face_bulk_testing_api, json=input_data)

    #     assert response.status_code == 200
    #     body = ResponseBody(**response.json())
    #     assert isinstance(body.root, TextResponse)
    #     print(f"Find face bulk testing result: {body.root.value}...")

    def test_08_delete_collection_endpoint(self):
        """Test the delete_collection endpoint to clean up our test collection"""
        # Check if our collection exists before trying to delete
        collections = DB.client.list_collections()
        collection_names = [col.name for col in collections]
        if self.__class__.full_collection_name not in collection_names:
            pytest.skip(
                f"Test collection {self.__class__.full_collection_name} not available to delete"
            )

        delete_collection_api = f"/{APP_NAME}/deletecollection"

        input_data = {
            "inputs": {},
            "parameters": {
                "collection_name": self.__class__.test_collection_name,
            },
        }

        response = self.client.post(delete_collection_api, json=input_data)

        assert response.status_code == 200
        body = ResponseBody(**response.json())
        assert isinstance(body.root, TextResponse)

        assert (
            "Successfully deleted" in body.root.value
            or "does not exist" in body.root.value
        ), f"Unexpected response: {body.root.value}"
        print(f"Delete collection result: {body.root.value}")

        # Only verify collection is gone if it was successfully deleted
        if "Successfully deleted" in body.root.value:
            collections = DB.client.list_collections()
            collection_names = [col.name for col in collections]
            assert (
                self.__class__.full_collection_name not in collection_names
            ), "Collection was not deleted"

    # def test_09_direct_vs_cli_commands(self):
    #     """Compare direct function calls with CLI commands"""

    #     print("\n===== Testing List Collections =====")
    #     # DIRECT: List collections directly from the DB
    #     db_collections = DB.client.list_collections()
    #     db_collection_names = [col.name for col in db_collections]
    #     print(f"Collections directly from DB: {db_collection_names}")

    #     # CLI: List collections via CLI
    #     cli_result = self.runner.invoke(
    #         self.cli_app, [f"/{APP_NAME}/listcollections", ""]
    #     )
    #     print(f"CLI exit code: {cli_result.exit_code}")
    #     print(f"CLI output: {cli_result.output}")

    #   # DIRECT: Test delete with non-existent collection by direct function call
    # print("\n===== Testing Delete Collection =====")
    # from face_detection_recognition.face_match_server import delete_collection_endpoint

    # test_params = {
    #     "collection_name": "nonexistent",
    # }

    # direct_result = delete_collection_endpoint(inputs = {}, parameters = test_params)
    # print(f"Direct function result: {direct_result.root.value}")
    # cli_delete_result = self.runner.invoke(
    #     self.cli_app,
    #     [f"/{APP_NAME}/deletecollection", "", "nonexistent"],
    # )
    # print(f"CLI delete exit code: {cli_delete_result.exit_code}")
    # print(f"CLI delete output: {cli_delete_result.output}")

    #     # Assert that direct call works as expected (contains error message)
    #     assert "does not exist" in direct_result.root.value

    #     # Just verify CLI runs without error (exit code 0)
    #     assert cli_result.exit_code == 0
    #     assert cli_delete_result.exit_code == 0

    #     print(
    #         "\nCOMPARISON: Direct function call returns detailed results, "
    #         "while CLI commands appear to be running successfully but not returning output."
    #     )

    def test_10_cli_parsers(self):
        """Test the CLI parser functions"""
        from face_detection_recognition.face_match_server import (
            face_find_cli_parser,
            face_find_param_parser,
            find_face_bulk_cli_parser,
            find_face_bulk_param_parser,
            bulk_upload_cli_parser,
            bulk_upload_param_parser,
            delete_collection_parameter_parser,
            list_collections_cli_parser,
        )

        # Test face_find_cli_parser
        input_str = f"{str(TEST_QUERY_IMAGE)}"
        parsed_input = face_find_cli_parser(input_str)
        assert "image_paths" in parsed_input
        assert len(parsed_input["image_paths"].files) == 1
        assert str(parsed_input["image_paths"].files[0].path) == str(TEST_QUERY_IMAGE)

        # Test face_find_param_parser
        param_str = f"{self.__class__.test_collection_name},0.5"
        parsed_params = face_find_param_parser(param_str)
        assert parsed_params["collection_name"] == self.__class__.test_collection_name
        assert parsed_params["similarity_threshold"] == 0.5

        # Test find_face_bulk_cli_parser
        dir_input = str(TEST_FACES_DIR)
        parsed_dir = find_face_bulk_cli_parser(dir_input)
        assert "query_directory" in parsed_dir
        assert str(parsed_dir["query_directory"].path) == dir_input

        # Test find_face_bulk_param_parser
        bulk_param_str = f"{self.__class__.test_collection_name},0.6"
        parsed_bulk_params = find_face_bulk_param_parser(bulk_param_str)
        assert (
            parsed_bulk_params["collection_name"] == self.__class__.test_collection_name
        )
        assert parsed_bulk_params["similarity_threshold"] == 0.6

        # Test bulk_upload_cli_parser
        upload_input = str(TEST_IMAGES_DIR)
        parsed_upload = bulk_upload_cli_parser(upload_input)
        assert "directory_path" in parsed_upload
        assert str(parsed_upload["directory_path"].path) == upload_input

        # Test bulk_upload_param_parser
        upload_param_str = "Create a new collection,test_collection"
        parsed_upload_params = bulk_upload_param_parser(upload_param_str)
        assert (
            parsed_upload_params["dropdown_collection_name"]
            == "Create a new collection"
        )
        assert parsed_upload_params["collection_name"] == "test_collection"

        # Test delete_collection_cli_parser
        delete_param_str = f"{self.__class__.test_collection_name}"
        parsed_delete_params = delete_collection_parameter_parser(delete_param_str)
        assert (
            parsed_delete_params["collection_name"]
            == self.__class__.test_collection_name.lower()
        )

        # Test list_collections_cli_parser (simple passthrough function)
        dummy_input = ""
        assert list_collections_cli_parser(dummy_input) == dummy_input

        print("All CLI parser functions tested successfully")


if __name__ == "__main__":
    unittest.main()
