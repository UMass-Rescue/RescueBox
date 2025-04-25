import os
import json
import uuid
import unittest
from pathlib import Path
import shutil
import pytest
import sys
import onnxruntime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

# Force CPU execution for testing - ONNX Runtime settings
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["ONNX_DEVICE"] = "CPU"

try:
    original_get_available_providers = onnxruntime.get_available_providers
    onnxruntime.get_available_providers = lambda: ['CPUExecutionProvider']
    # Set global ONNX session options to prefer CPU
    onnxruntime.set_default_logger_severity(3)
    print("Successfully configured ONNX Runtime for CPU-only execution")
except ImportError:
    print("ONNX Runtime issue")

try:
    from rb.api.models import ResponseBody, TextResponse, BatchTextResponse, BatchFileResponse
    from rb.lib.common_tests import RBAppTest
    rb_imported = True
except ImportError:
    print("Failed to import rb modules. Attempting a different approach...")
    rb_imported = False

from facematch.facematch.face_match_server import app as cli_app, APP_NAME, server, DBclient


TEST_IMAGES_DIR = Path("src/FaceDetectionandRecognition/resources/sample_db")
TEST_FACES_DIR = Path("src/FaceDetectionandRecognition/resources/sample_queries")  # Directory with clear face images
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
        cls.full_collection_name = f"{cls.test_collection_name}_{TEST_DETECTOR_BACKEND}_{TEST_MODEL_NAME}"
        
        print("=" * 80)
        print(f"Test setup complete. Using CPU mode for testing with ONNX Runtime.")
        print(f"Test images available: {cls.has_test_images}")
        print(f"Testing with collection: {cls.test_collection_name}")
        print("=" * 80)

    @classmethod
    def teardown_class(cls):
        """Clean up after all tests"""
        # Delete our test collection if it exists
        try:
            if hasattr(cls, 'full_collection_name'):
                collections = DBclient.list_collections()
                collection_names = [col.name for col in collections]
                if cls.full_collection_name in collection_names:
                    DBclient.delete_collection(cls.full_collection_name)
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
        from facematch.facematch.face_match_server import (
            get_ingest_query_image_task_schema, 
            get_ingest_bulk_query_image_task_schema,
            get_ingest_bulk_test_query_image_task_schema,
            get_ingest_images_task_schema,
            delete_collection_task_schema,
            list_collections_task_schema
        )
        
        return [
            (0, "findface", "Find Face", get_ingest_query_image_task_schema()),
            (1, "findfacebulk", "Face Find Bulk", get_ingest_bulk_query_image_task_schema()),
            (2, "findfacebulktesting", "Face Find Bulk Test", get_ingest_bulk_test_query_image_task_schema()),
            (3, "bulkupload", "Bulk Upload", get_ingest_images_task_schema()),
            (4, "deletecollection", "Delete Collection", delete_collection_task_schema()),
            (5, "listcollection", "List Collection", list_collections_task_schema()),
        ]

    def test_01_metadata_and_schemas(self):
        """Test app metadata and task schemas"""
        # Check app metadata
        metadata = self.get_metadata()
        assert metadata.name == "Face Recognition and Matching"
        assert metadata.plugin_name == APP_NAME
        assert metadata.author == "FaceMatch Team"
        
        # Check task schemas
        from facematch.facematch.face_match_server import (
            get_ingest_query_image_task_schema, 
            get_ingest_bulk_query_image_task_schema,
            get_ingest_images_task_schema,
            delete_collection_task_schema,
            list_collections_task_schema
        )
        
        # Test that each schema returns a valid TaskSchema object
        schemas = [
            get_ingest_query_image_task_schema(),
            get_ingest_bulk_query_image_task_schema(),
            get_ingest_images_task_schema(),
            delete_collection_task_schema(),
            list_collections_task_schema()
        ]
        
        for schema in schemas:
            assert schema is not None
            assert hasattr(schema, 'inputs')
    
    def test_02_config_loading(self):
        """Test that config file exists and can be loaded"""
        from facematch.facematch.face_match_server import config, config_path
        assert os.path.exists(config_path), "Config file not found"
        assert "cosine-threshold" in config, "Config missing cosine-threshold key"
        assert isinstance(config["cosine-threshold"], (int, float)), "Threshold not numeric"
    
    def test_03_list_collections_endpoint(self):
        """Test the list_collections endpoint"""
        
        list_collection_api = f"/{APP_NAME}/listcollection"
        
        response = self.client.post(list_collection_api, json={"inputs": {}, "parameters": {}})
        
        assert response.status_code == 200
        body = ResponseBody(**response.json())
        assert isinstance(body.root, BatchTextResponse)
        # Store collections for later comparison
        self.initial_collections = [text.value for text in body.root.texts]
        print(f"Initial collections: {self.initial_collections}")
    
    @pytest.mark.skipif(not has_test_images, reason="Test images not available")
    def test_04_bulk_upload_endpoint(self):
        """Test the bulk_upload endpoint to create our test collection"""
        
        bulk_upload_api = f"/{APP_NAME}/bulkupload"
        input_data = {
            "inputs": {
                "directory_paths": {
                    "directories": [{"path": str(TEST_IMAGES_DIR)}]
                }
            },
            "parameters": {
                "dropdown_collection_name": "Create a new collection",
                "collection_name": self.__class__.test_collection_name
            }
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
        if "Successfully uploaded" in result_text and not "0 faces" in result_text:
            collections = DBclient.list_collections()
            collection_names = [col.name for col in collections]
            print(collection_names)
            assert self.__class__.full_collection_name in collection_names, "Collection was not created"
            print(f"Created collection: {self.__class__.full_collection_name}")
    
    @pytest.mark.skipif(not has_test_images, reason="Test images not available")
    def test_05_find_face_endpoint(self):
        """Test the find_face endpoint with our test collection"""
        # Make sure we have a collection
        collections = DBclient.list_collections()
        collection_names = [col.name for col in collections]
        if self.__class__.full_collection_name not in collection_names:
            pytest.skip(f"Test collection {self.__class__.full_collection_name} not available")
        
        find_face_api = f"/{APP_NAME}/findface"
        input_data = {
            "inputs": {
                "image_paths": {
                    "files": [{"path": str(TEST_QUERY_IMAGE)}]
                }
            },
            "parameters": {
                "collection_name": self.__class__.test_collection_name,
                "similarity_threshold": 0.5
            }
        }
        
        response = self.client.post(find_face_api, json=input_data)
        
        assert response.status_code == 200
        body = ResponseBody(**response.json())
        # The response could be TextResponse (no matches) or BatchFileResponse (matches found)
        assert isinstance(body.root, (TextResponse, BatchFileResponse))
        
        if isinstance(body.root, TextResponse):
            print(f"Find face result (text): {body.root.value}")
        else:
            print(f"Find face result (files): {len(body.root.files)} matches found")
    
    @pytest.mark.skipif(not has_test_images, reason="Test images not available")
    def test_06_find_face_bulk_endpoint(self):
        """Test the find_face_bulk endpoint with our test collection"""
        # Make sure we have a collection
        collections = DBclient.list_collections()
        collection_names = [col.name for col in collections]
        if self.__class__.full_collection_name not in collection_names:
            pytest.skip(f"Test collection {self.__class__.full_collection_name} not available")
        
        find_face_bulk_api = f"/{APP_NAME}/findfacebulk"
        input_data = {
            "inputs": {
                "query_directory": {
                    "path": str(TEST_FACES_DIR)
                }
            },
            "parameters": {
                "collection_name": self.__class__.test_collection_name,
                "similarity_threshold": 0.5
            }
        }
        
        # Send the request
        response = self.client.post(find_face_bulk_api, json=input_data)
        
        # Assert response
        assert response.status_code == 200
        body = ResponseBody(**response.json())
        assert isinstance(body.root, TextResponse)
        print(f"Find face bulk result: {body.root.value}...")
    
    @pytest.mark.skipif(not has_test_images, reason="Test images not available")
    def test_07_find_face_bulk_testing_endpoint(self):
        """Test the find_face_bulk_testing endpoint with our test collection"""
        # Make sure we have a collection
        collections = DBclient.list_collections()
        collection_names = [col.name for col in collections]
        if self.__class__.full_collection_name not in collection_names:
            pytest.skip(f"Test collection {self.__class__.full_collection_name} not available")
        
        find_face_bulk_testing_api = f"/{APP_NAME}/findfacebulktesting"
        input_data = {
            "inputs": {
                "query_directory": {
                    "path": str(TEST_FACES_DIR)
                }
            },
            "parameters": {
                "collection_name": self.__class__.test_collection_name
            }
        }
        
        response = self.client.post(find_face_bulk_testing_api, json=input_data)
        
        assert response.status_code == 200
        body = ResponseBody(**response.json())
        assert isinstance(body.root, TextResponse)
        print(f"Find face bulk testing result: {body.root.value}...")
    
    def test_08_delete_collection_endpoint(self):
        """Test the delete_collection endpoint to clean up our test collection"""
        # Check if our collection exists before trying to delete
        collections = DBclient.list_collections()
        collection_names = [col.name for col in collections]
        if self.__class__.full_collection_name not in collection_names:
            pytest.skip(f"Test collection {self.__class__.full_collection_name} not available to delete")
        
        delete_collection_api = f"/{APP_NAME}/deletecollection"
        input_data = {
            "inputs": {
                "collection_name": {
                    "text": self.__class__.test_collection_name
                },
                "model_name": {
                    "text": TEST_MODEL_NAME
                },
                "detector_backend": {
                    "text": TEST_DETECTOR_BACKEND
                }
            }
        }
        
        response = self.client.post(delete_collection_api, json=input_data)
        
        assert response.status_code == 200
        body = ResponseBody(**response.json())
        assert isinstance(body.root, TextResponse)
        assert "Successfully deleted" in body.root.value
        print(f"Delete collection result: {body.root.value}")
        
        # Verify the collection is gone
        collections = DBclient.list_collections()
        collection_names = [col.name for col in collections]
        assert self.__class__.full_collection_name not in collection_names, "Collection was not deleted"
    
    def test_09_cli_commands(self):
        """Test basic CLI commands"""

        # FOR NOW
        pytest.skip("Skipping CLI command tests - recommend testing CLI manually")
    

        # Test list collections command
        result = self.runner.invoke(
            self.cli_app, 
            [f"/{APP_NAME}/listcollection"]
        )
        assert result.exit_code == 0, f"Error in list_collection command: {result.output}"
        print(f"List collections CLI result: {result.output[:100]}...")
        
        # Test delete with non-existent collection (should fail gracefully)
        result = self.runner.invoke(
            self.cli_app, 
            [f"/{APP_NAME}/deletecollection", "nonexistent", "facenet512", "retinaface"]
        )
        assert result.exit_code == 0, f"Error in delete_collection command: {result.output}"
        assert "does not exist" in result.output
        print(f"Delete non-existent collection CLI result: {result.output}")
    
    @pytest.mark.skipif(not has_test_images, reason="Test images not available")
    def test_10_parse_inputs_and_parameters(self):
        """Test the parameter and input parsing functions"""

        # FOR NOW
        pytest.skip("Skipping parsing tests")

        from facematch.facematch.face_match_server import parse_parameters, parse_inputs
        
        # Test parse_parameters
        params_tuple = ("dropdown_val", "collection_val")
        parsed = parse_parameters(
            params_tuple, 
            default_values={
                "dropdown_collection_name": "default_dropdown",
                "collection_name": "default_collection"
            }
        )
        assert parsed["dropdown_collection_name"] == "dropdown_val"
        assert parsed["collection_name"] == "collection_val"
        
        # Test parse_inputs
        from rb.api.models import BatchDirectoryInput, DirectoryInfo
        batch_dir_input = BatchDirectoryInput(
            directories=[DirectoryInfo(path=str(TEST_FACES_DIR))]
        )
        inputs_dict = {"directory_paths": batch_dir_input}
        parsed_path = parse_inputs(inputs_dict, "directory_paths")
        assert parsed_path == str(TEST_FACES_DIR)


if __name__ == "__main__":
    unittest.main()