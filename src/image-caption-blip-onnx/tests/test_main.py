from unittest.mock import MagicMock
import pytest
from pathlib import Path

from rb.lib.common_tests import RBAppTest
from rb.api.models import AppMetadata, TaskSchema

# Since we are refactoring, we need to import the app from the refactored main
from image_caption_blip_onnx.main import app, APP_NAME, captioning_task_schema, generate_caption

@pytest.fixture
def mock_onnx_and_processor(mocker):
    """Mocks the ONNX sessions and the Transformers processor."""
    mocker.patch("image_caption_blip_onnx.main.load_models", return_value=None)
    mocker.patch("image_caption_blip_onnx.main.vision_session.run", return_value=["mocked_image_embeds"])
    mocker.patch("image_caption_blip_onnx.main.text_session.run", return_value=[[1, 2, 3]])
    
    mock_processor = MagicMock()
    mock_processor.decode.return_value = "A mocked BLIP caption."
    mocker.patch("image_caption_blip_onnx.main.processor", mock_processor)

@pytest.fixture
def dummy_image_file(tmp_path):
    """Creates a dummy image file for testing."""
    dummy_file = tmp_path / "test_image.png"
    from PIL import Image
    Image.new('RGB', (1, 1)).save(dummy_file, 'PNG')
    return dummy_file

class TestBlipCaptioning(RBAppTest):
    def setup_class(self):
        self.set_app(app, APP_NAME)

    def get_metadata(self) -> AppMetadata:
        # This should be defined in the main app, but we can mock it for the test
        return AppMetadata(
            name="Image Captioning (BLIP/ONNX)",
            author="RescueBox",
            version="0.1.0",
            info="Generates captions for images using a BLIP ONNX model.",
            plugin_name=APP_NAME,
        )

    def get_all_ml_services(self):
        return [
            (1, "/caption", "Generate Image Caption", captioning_task_schema()),
        ]

    def test_generate_caption_logic(self, mock_onnx_and_processor, dummy_image_file):
        """Directly tests the logic of the generate_caption function."""
        inputs = {"image_file": {"path": dummy_image_file}}
        response = generate_caption(inputs)
        assert response.value == "A mocked BLIP caption."

    def test_cli_caption_command(self, mock_onnx_and_processor, dummy_image_file, caplog):
        """Tests the full CLI command."""
        with caplog.at_level("INFO"):
            result = self.runner.invoke(self.cli_app, ["/caption", str(dummy_image_file)])
            assert result.exit_code == 0
            # The actual response is now a JSON object, so we check the log
            assert "A mocked BLIP caption." in caplog.text