"""
Unit tests for multiple tool call handling and chaining functionality.

This module tests the complex multi-tool call orchestration system that enables
chaining outputs from one tool as inputs to subsequent tools. It validates:

- Output path extraction from various response types
- Input/output chaining between tool calls
- Multi-tool call result aggregation
- Granite model interactions with multiple tool calls
- Message handler coordination for complex tool workflows

The tests ensure that complex tool chains work reliably and that outputs
are properly routed between sequential tool executions.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rb.api.models import (
    DirectoryResponse,
    FloatParameterDescriptor,
    InputSchema,
    InputType,
    ParameterSchema,
    ResponseBody,
    TaskSchema,
    TextResponse,
)

from frontend.chatbot.config import ChatbotConfig
from frontend.chatbot.core import ChatbotCore
from frontend.chatbot.multi_tool_handler import (
    MultiToolCallResult,
    chain_output_to_input,
    extract_output_path,
)

# Test constants
TEST_OUTPUT_DIR = '/output/summaries'
TEST_RESULTS_DIR = '/output/results'
TEST_IMAGES_DIR = '/output/images'
TEST_IMAGE_PATH = '/output/images/photo.jpg'
TEST_BATCH_IMAGE_PATH = '/output/images/photo1.jpg'
TEST_TEXT_VALUE = 'Some text'
TEST_TOOL_NAME = 'test/tool'


class TestExtractOutputPath:
    """Tests for extract_output_path function.

    This class validates that output paths can be correctly extracted
    from various response types, enabling proper chaining of tool outputs
    to subsequent tool inputs in multi-tool workflows.
    """

    def test_extract_from_batch_directory_response(self):
        """Test extracting path from BatchDirectoryResponse.

        Validates that when a tool produces multiple directories as output,
        the system can extract the primary output directory path for
        chaining to subsequent tools that need directory inputs.
        """
        from rb.api.models import DirectoryResponse, BatchDirectoryResponse, ResponseBody

        dir_response = DirectoryResponse(
            output_type='directory',
            path=TEST_OUTPUT_DIR,
            title='Summaries'
        )
        batch_dir = BatchDirectoryResponse(directories=[dir_response])
        response_body = ResponseBody(root=batch_dir)

        result = extract_output_path(response_body)
        assert result == TEST_OUTPUT_DIR
    
    def test_extract_from_directory_response(self):
        """Test extracting path from DirectoryResponse.

        Ensures that single directory outputs are properly handled
        and their paths extracted for use as inputs to subsequent tools.
        """
        from rb.api.models import DirectoryResponse, ResponseBody

        dir_response = DirectoryResponse(
            output_type='directory',
            path=TEST_RESULTS_DIR,
            title='Results'
        )
        response_body = ResponseBody(root=dir_response)

        result = extract_output_path(response_body)
        assert result == TEST_RESULTS_DIR

    def test_extract_from_batch_file_response(self):
        """Test extracting parent directory from BatchFileResponse.

        Validates that when multiple files are produced, the system
        extracts the common parent directory path, allowing subsequent
        tools to process the entire directory of generated files.
        """
        from rb.api.models import FileResponse, BatchFileResponse, ResponseBody

        file_response = FileResponse(
            output_type='file',
            file_type='img',
            path=TEST_BATCH_IMAGE_PATH,
            title='Photo 1'
        )
        batch_file = BatchFileResponse(files=[file_response])
        response_body = ResponseBody(root=batch_file)

        result = extract_output_path(response_body)
        assert result == TEST_IMAGES_DIR

    def test_extract_from_batch_text_response_transcripts_dir(self):
        """audio/transcribe writes .txt under transcripts_dir; chain uses that path."""
        from rb.api.models import BatchTextResponse, ResponseBody, TextResponse

        td = "/cases/audio_in/transcripts"
        batch = BatchTextResponse(
            texts=[TextResponse(value="hello", title="/cases/audio_in/x.mp3")],
            transcripts_dir=td,
        )
        response_body = ResponseBody(root=batch)
        result = extract_output_path(response_body)
        assert result == td

    def test_extract_from_ufdr_mount_message(self):
        """ufdr_mounter returns TextResponse 'Mounted at /tmp/case1'; chain uses .../files/."""
        from rb.api.models import TextResponse, ResponseBody

        response_body = ResponseBody(
            root=TextResponse(value="Mounted at /tmp/case1", title="Mount Result")
        )
        result = extract_output_path(response_body)
        assert result == "/tmp/case1/files"

    def test_extract_from_file_response(self):
        """Test extracting parent directory from FileResponse.

        Confirms that single file outputs are handled by extracting
        the containing directory, enabling tools that need to work
        with the file's directory context.
        """
        from rb.api.models import FileResponse, ResponseBody

        file_response = FileResponse(
            output_type='file',
            file_type='img',
            path=TEST_IMAGE_PATH,
            title='Photo'
        )
        response_body = ResponseBody(root=file_response)

        result = extract_output_path(response_body)
        assert result == TEST_IMAGES_DIR
    
    def test_extract_none_when_no_path(self):
        """Test returning None when path cannot be extracted.

        Ensures that response types without extractable file system paths
        (like text responses) return None, preventing invalid path chaining
        and maintaining system stability for non-file-based outputs.
        """
        from rb.api.models import TextResponse, ResponseBody

        text_response = TextResponse(
            output_type='text',
            value=TEST_TEXT_VALUE,
            title='Text'
        )
        response_body = ResponseBody(root=text_response)

        result = extract_output_path(response_body)
        assert result is None


class TestChainOutputToInput:
    """Tests for chain_output_to_input function.

    This class validates the output-to-input chaining mechanism that
    automatically connects the outputs of one tool as inputs to the
    next tool in a multi-tool workflow, enabling complex processing
    pipelines without manual intervention.
    """
    
    def test_chain_directory_output_to_input_dir(self):
        """Test chaining directory output to input directory field"""
        # Previous output with directory
        dir_response = DirectoryResponse(
            output_type='directory',
            path='/output/summaries',
            title='Summaries'
        )
        previous_output = ResponseBody(root=dir_response)
        
        # Current schema with input_dir field
        current_schema = TaskSchema(
            inputs=[
                InputSchema(
                    key='input_dir',
                    label='Input Directory',
                    input_type=InputType.DIRECTORY
                )
            ],
            parameters=[]
        )
        
        # Current arguments
        current_arguments = {'input_dir': '/tmp'}
        
        # Chain output
        result = chain_output_to_input(previous_output, current_arguments, current_schema)
        
        assert result['input_dir'] == '/output/summaries'

    def test_chain_image_summary_to_text_search_injects_file_filter_without_schema_row(self):
        """Public GET task_schema omits file_filter; chaining must still set explicit paths."""
        import json
        from rb.api.models import TextResponse

        out_txt = "/demo/outputs/a.png.txt"
        payload = {
            "image_summary": True,
            "input_dir": "/demo/in",
            "files": [out_txt],
        }
        previous_output = ResponseBody(
            root=TextResponse(value=json.dumps(payload), title="Summaries")
        )
        # Schema like text-embeddings public API: only input_dir + query (no file_filter key).
        current_schema = TaskSchema(
            inputs=[
                InputSchema(key="input_dir", label="In", input_type=InputType.DIRECTORY),
                InputSchema(key="query", label="Q", input_type=InputType.TEXT),
            ],
            parameters=[],
        )
        result = chain_output_to_input(previous_output, {}, current_schema)
        assert result["input_dir"] == Path(out_txt).parent.as_posix()
        assert result["file_filter"]["files"] == [{"path": out_txt}]

    def test_chain_transcribe_to_summarize_defaults_output_dir(self):
        """After transcribe, transcripts_dir chains to input_dir; output_dir defaults beside transcripts."""
        from rb.api.models import BatchTextResponse, TextResponse

        transcripts = "/evidence/audio_in/transcripts"
        previous_output = ResponseBody(
            root=BatchTextResponse(
                texts=[TextResponse(value="hi", title="/evidence/audio_in/a.mp3")],
                transcripts_dir=transcripts,
            )
        )
        current_schema = TaskSchema(
            inputs=[
                InputSchema(
                    key="input_dir",
                    label="Input",
                    input_type=InputType.DIRECTORY,
                ),
                InputSchema(
                    key="output_dir",
                    label="Output",
                    input_type=InputType.DIRECTORY,
                ),
            ],
            parameters=[],
        )
        result = chain_output_to_input(previous_output, {}, current_schema)
        assert result["input_dir"] == transcripts
        assert result["output_dir"] == transcripts

    def test_chain_after_ufdr_mount_sets_input_dir_files(self):
        """After UFDR mount, next tool input_dir is mount point + /files."""
        from rb.api.models import TextResponse

        previous_output = ResponseBody(
            root=TextResponse(value="Mounted at /tmp/case1", title="Mount Result")
        )
        current_schema = TaskSchema(
            inputs=[
                InputSchema(
                    key="input_dir",
                    label="Input",
                    input_type=InputType.DIRECTORY,
                )
            ],
            parameters=[],
        )
        result = chain_output_to_input(previous_output, {}, current_schema)
        assert result["input_dir"] == "/tmp/case1/files"

    def test_chain_to_input_dataset(self):
        """Test chaining to input_dataset field"""
        dir_response = DirectoryResponse(
            output_type='directory',
            path='/output/results',
            title='Results'
        )
        previous_output = ResponseBody(root=dir_response)
        
        current_schema = TaskSchema(
            inputs=[
                InputSchema(
                    key='input_dataset',
                    label='Input Dataset',
                    input_type=InputType.DIRECTORY
                )
            ],
            parameters=[]
        )
        
        current_arguments = {'input_dataset': '/tmp'}
        
        result = chain_output_to_input(previous_output, current_arguments, current_schema)
        
        assert result['input_dataset'] == '/output/results'
    
    def test_preserve_other_arguments(self):
        """Test that other arguments are preserved"""
        dir_response = DirectoryResponse(
            output_type='directory',
            path='/output/summaries',
            title='Summaries'
        )
        previous_output = ResponseBody(root=dir_response)
        
        current_schema = TaskSchema(
            inputs=[
                InputSchema(
                    key='input_dir',
                    label='Input Directory',
                    input_type=InputType.DIRECTORY
                )
            ],
            parameters=[
                ParameterSchema(
                    key='confidence',
                    label='Confidence',
                    value=FloatParameterDescriptor(default=0.5)
                )
            ]
        )
        
        current_arguments = {
            'input_dir': '/tmp',
            'confidence': 0.8
        }
        
        result = chain_output_to_input(previous_output, current_arguments, current_schema)
        
        assert result['input_dir'] == '/output/summaries'
        assert result['confidence'] == 0.8
    
    def test_no_chaining_when_no_output_path(self):
        """Test that arguments remain unchanged when no output path can be extracted"""
        
        text_response = TextResponse(
            output_type='text',
            value='Some text',
            title='Text'
        )
        previous_output = ResponseBody(root=text_response)
        
        current_schema = TaskSchema(
            inputs=[
                InputSchema(
                    key='input_dir',
                    label='Input Directory',
                    input_type=InputType.DIRECTORY
                )
            ],
            parameters=[]
        )
        
        current_arguments = {'input_dir': '/tmp'}
        
        result = chain_output_to_input(previous_output, current_arguments, current_schema)
        
        # Should remain unchanged
        assert result['input_dir'] == '/tmp'
    
    def test_no_chaining_when_no_input_dir_field(self):
        """Test that arguments remain unchanged when no input directory field exists"""
        dir_response = DirectoryResponse(
            output_type='directory',
            path='/output/summaries',
            title='Summaries'
        )
        previous_output = ResponseBody(root=dir_response)
        
        # Schema without input directory field
        current_schema = TaskSchema(
            inputs=[
                InputSchema(
                    key='prompt',
                    label='Prompt',
                    input_type=InputType.TEXT
                )
            ],
            parameters=[]
        )
        
        current_arguments = {'prompt': 'test'}
        
        result = chain_output_to_input(previous_output, current_arguments, current_schema)
        
        # Should remain unchanged
        assert result == current_arguments


class TestMultiToolCallResult:
    """Tests for MultiToolCallResult class"""
    
    def test_initialization(self):
        """Test MultiToolCallResult initialization"""
        result = MultiToolCallResult()
        assert result.tool_calls == []
        assert result.results == []
        assert result.errors == []
        assert result.completed_count == 0
    
    def test_add_result_success(self):
        """Test adding successful result"""
        result = MultiToolCallResult()
        
        tool_call = {'endpoint': 'audio/transcribe', 'arguments': {}}
        response_body = ResponseBody(root=DirectoryResponse(
            output_type='directory',
            path='/output',
            title='Output'
        ))
        
        result.add_result(tool_call, response_body, None)
        
        assert len(result.tool_calls) == 1
        assert len(result.results) == 1
        assert len(result.errors) == 1
        assert result.completed_count == 1
        assert result.errors[0] is None
    
    def test_add_result_error(self):
        """Test adding result with error"""
        result = MultiToolCallResult()
        
        tool_call = {'endpoint': 'test/endpoint', 'arguments': {}}
        error = 'Test error'
        
        result.add_result(tool_call, None, error)
        
        assert len(result.tool_calls) == 1
        assert result.results[0] is None
        assert result.errors[0] == error
        assert result.completed_count == 0


class TestCallGraniteModelMultipleCalls:
    """Tests for call_granite_model with multiple tool calls"""

    @staticmethod
    def _ollama_resp(content: str):
        m = MagicMock()
        m.status_code = 200
        m.json.return_value = {"message": {"content": content}}
        return m

    @pytest.fixture
    def core(self):
        """Create ChatbotCore instance"""
        config = ChatbotConfig()
        return ChatbotCore(config)

    @pytest.mark.asyncio
    async def test_extract_multiple_tool_calls_from_tags(self, core):
        """Test extracting multiple tool calls from <tool_code> tags"""
        content = """
            Here are the tool calls:
            <tool_code>{"name": "image_summary/summarize-images", "arguments": {"input_dir": "/tmp"}}</tool_code>
            <tool_code>{"name": "deepfake_detection/predict", "arguments": {"input_dataset": "/tmp"}}</tool_code>
            """
        core.ollama_client.post = AsyncMock(return_value=self._ollama_resp(content))

        result = await core.call_granite_model("summarize and detect fakes")

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "image_summary/summarize-images"
        assert result[0]["arguments"]["input_dir"] == "/tmp"
        assert result[1]["name"] == "deepfake_detection/predict"
        assert result[1]["arguments"]["input_dataset"] == "/tmp"

    @pytest.mark.asyncio
    async def test_extract_single_tool_call(self, core):
        """Test backward compatibility with single tool call"""
        content = """
            <tool_code>{"name": "audio/transcribe", "arguments": {"input_dir": "/tmp"}}</tool_code>
            """
        core.ollama_client.post = AsyncMock(return_value=self._ollama_resp(content))

        result = await core.call_granite_model("transcribe audio")

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "audio/transcribe"

    @pytest.mark.asyncio
    async def test_no_tool_calls_found(self, core):
        """Test when no tool calls are found"""
        core.ollama_client.post = AsyncMock(
            return_value=self._ollama_resp("I cannot help with that request.")
        )

        result = await core.call_granite_model("some request")

        assert result is None

    @pytest.mark.asyncio
    async def test_extract_multiple_json_objects(self, core):
        """Test extracting multiple tool calls from raw JSON format (brace scan)."""
        content = """
            {"name": "image_summary/summarize-images", "arguments": {"input_dir": "/tmp"}}
            {"name": "deepfake_detection/predict", "arguments": {"input_dataset": "/tmp"}}
            """
        core.ollama_client.post = AsyncMock(return_value=self._ollama_resp(content))

        result = await core.call_granite_model("summarize and detect")

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 2


class TestMessageHandlerMultipleCalls:
    """Tests for message handler with multiple tool calls"""
    
    @pytest.fixture
    def handler(self):
        """Create MessageHandler instance"""
        from frontend.chatbot.message_handler import MessageHandler
        from frontend.chatbot.config import ChatbotConfig
        from frontend.chatbot.core import ChatbotCore
        
        config = ChatbotConfig()
        core = ChatbotCore(config)
        return MessageHandler(core, config)
    
    @pytest.mark.asyncio
    async def test_handle_multiple_tool_calls(self, handler):
        """Test handling multiple tool calls"""
        # Mock call_granite_model to return multiple tool calls
        multiple_calls = [
            {"name": "image_summary/summarize-images", "arguments": {"input_dir": "/tmp"}},
            {"name": "deepfake_detection/predict", "arguments": {"input_dataset": "/tmp"}},
        ]

        with patch.object(handler.core, "call_granite_model_direct", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = multiple_calls

            result = await handler.handle_smart_analyze("summarize images and detect fakes")

            assert result["type"] == "multi_tool_calls"
            assert "tool_calls" in result
            assert len(result["tool_calls"]) == 2
            assert result["tool_calls"][0]["endpoint"] == "image_summary/summarize-images"
            assert result["tool_calls"][1]["endpoint"] == "deepfake_detection/predict"
    
    @pytest.mark.asyncio
    async def test_handle_single_tool_call_backward_compat(self, handler):
        """Test backward compatibility with single tool call"""
        single_call = [
            {'name': 'audio/transcribe', 'arguments': {'input_dir': '/tmp'}}
        ]
        
        with patch.object(handler.core, 'call_granite_model_direct', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = single_call
            
            result = await handler.handle_smart_analyze("transcribe audio")
            
            # Should return 'show_form' type for single call (backward compatible)
            assert result['type'] == 'show_form'
            assert result['endpoint'] == 'audio/transcribe'
            assert 'arguments' in result


class TestBatchMetadataFilterGate:
    """Pipeline filter dialog should only apply when prior step has Age/Gender metadata."""

    def test_clip_search_rows_do_not_trigger_age_gender_filter(self):
        from frontend.chatbot.multi_tool_handler import batch_items_have_age_gender_metadata

        items = [
            {
                "path": "/photos/a.jpg",
                "metadata": {
                    "Query": "young girl",
                    "Similarity": "0.2598",
                    "Match": "Yes",
                    "Model": "openai/clip-vit-base-patch32",
                },
            },
        ]
        assert batch_items_have_age_gender_metadata(items) is False

    def test_age_gender_classifier_rows_trigger_filter(self):
        from frontend.chatbot.multi_tool_handler import batch_items_have_age_gender_metadata

        items = [
            {"path": "/photos/a.jpg", "metadata": {"Gender": "Female", "Age": "(4-6)"}},
        ]
        assert batch_items_have_age_gender_metadata(items) is True
