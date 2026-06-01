"""
Unit tests for form data validation functionality.

This module tests the validation system that ensures form data conforms
to task schema requirements, including parameter ranges, input types,
and data integrity checks.
"""

from pathlib import Path
from typing import cast

import pytest
from rb.api.models import DirectoryInput, ResponseBody

from frontend.utils import (
    _create_input_model,
    _validate_parameter_value,
    validate_form_data,
    validate_response_body,
)


class TestValidateFormData:
    """Tests for validate_form_data (inputs + optional raster; parameters pass-through)."""

    def test_validate_valid_form_data(self, sample_task_schema, temp_directory):
        """Test validation of valid form data.

        Verifies that well-formed form data passes all validation checks
        and returns a successful validation result.
        """
        form_data = {
            'inputs': {
                'input_dir': {'path': str(temp_directory)},
                'prompt': {'text': 'Test prompt'}
            },
            'parameters': {
                'confidence': 0.85,
                'mode': 'fast'
            }
        }
        
        result = validate_form_data(form_data, sample_task_schema)
        
        assert result['is_valid'] is True
        assert len(result['errors']) == 0
        assert 'validated_data' in result
    
    def test_validate_invalid_directory(self, sample_task_schema):
        """Test validation fails with invalid directory path"""
        form_data = {
            'inputs': {
                'input_dir': {'path': '/nonexistent/path'},
                'prompt': {'text': 'Test'}
            },
            'parameters': {}
        }
        
        result = validate_form_data(form_data, sample_task_schema)
        
        # Should fail validation due to invalid path
        assert result['is_valid'] is False
        assert 'input_dir' in result['errors']

    def test_validate_missing_input_dir(self, sample_task_schema):
        """Submitting without a declared input path must fail before RequestBody."""
        form_data = {
            'inputs': {'prompt': {'text': 'Test'}},
            'parameters': {},
        }
        result = validate_form_data(form_data, sample_task_schema)
        assert result['is_valid'] is False
        assert 'input_dir' in result['errors']

    def test_validate_empty_directory_path(self, sample_task_schema):
        """Empty path string must be rejected for directory inputs."""
        form_data = {
            'inputs': {
                'input_dir': {'path': '   '},
                'prompt': {'text': 'Test'},
            },
            'parameters': {},
        }
        result = validate_form_data(form_data, sample_task_schema)
        assert result['is_valid'] is False
        assert 'input_dir' in result['errors']

    def test_query_text_input_must_not_be_empty(self, tmp_path):
        """image_embeddings/search_images (and similar) require a non-blank ``query`` input."""
        from rb.api.models import (
            TaskSchema,
            InputSchema,
            ParameterSchema,
            InputType,
            EnumParameterDescriptor,
            EnumVal,
        )

        corpus = tmp_path / "corpus"
        corpus.mkdir()
        (corpus / "note.txt").write_text("x")
        schema = TaskSchema(
            inputs=[
                InputSchema(
                    key="input_dir",
                    label="Folder of files to search",
                    inputType=InputType.DIRECTORY,
                ),
                InputSchema(
                    key="query",
                    label="Text query to find the most similar images",
                    inputType=InputType.TEXT,
                ),
            ],
            parameters=[
                ParameterSchema(
                    key="model",
                    label="Model",
                    value=EnumParameterDescriptor(
                        enumVals=[EnumVal(key="m", value="m", label="m")],
                        default="m",
                    ),
                )
            ],
        )
        base = {
            "inputs": {
                "input_dir": {"path": str(corpus)},
                "query": {"text": "   "},
            },
            "parameters": {"model": "m"},
        }
        empty = validate_form_data(dict(base), schema)
        assert empty["is_valid"] is False
        assert "query" in empty["errors"]
        assert "search" in empty["errors"]["query"].lower()

        ok = validate_form_data(
            {
                "inputs": {
                    "input_dir": {"path": str(corpus)},
                    "query": {"text": "person in red"},
                },
                "parameters": {"model": "m"},
            },
            schema,
        )
        assert ok["is_valid"] is True

    def test_image_endpoint_rejects_dir_without_image_files(self, tmp_path):
        """Raster rule follows schema copy: directory labeled for images must contain rasters."""
        from rb.api.models import (
            TaskSchema,
            InputSchema,
            ParameterSchema,
            InputType,
            RangedFloatParameterDescriptor,
            FloatRangeDescriptor,
            EnumParameterDescriptor,
            EnumVal,
        )

        schema = TaskSchema(
            inputs=[
                InputSchema(
                    key="input_dir",
                    label="Path to the directory containing the input images",
                    inputType=InputType.DIRECTORY,
                ),
                InputSchema(key="prompt", label="Prompt", inputType=InputType.TEXT),
            ],
            parameters=[
                ParameterSchema(
                    key="confidence",
                    label="Confidence",
                    value=RangedFloatParameterDescriptor(
                        range=FloatRangeDescriptor(min=0.0, max=1.0),
                        default=0.8,
                    ),
                ),
                ParameterSchema(
                    key="mode",
                    label="Processing Mode",
                    value=EnumParameterDescriptor(
                        enumVals=[
                            EnumVal(key="fast", value="fast", label="Fast"),
                            EnumVal(key="accurate", value="accurate", label="Accurate"),
                        ],
                        default="fast",
                    ),
                ),
            ],
        )
        d = tmp_path / "evidence"
        d.mkdir()
        (d / "notes.txt").write_text("no images")
        form_data = {
            'inputs': {'input_dir': {'path': str(d)}, 'prompt': {'text': 'captions'}},
            'parameters': {'confidence': 0.8, 'mode': 'fast'},
        }
        result = validate_form_data(form_data, schema)
        assert result['is_valid'] is False
        assert 'input_dir' in result['errors']
        assert 'image' in result['errors']['input_dir'].lower()

    def test_image_endpoint_accepts_dir_with_jpeg(self, tmp_path):
        from rb.api.models import (
            TaskSchema,
            InputSchema,
            ParameterSchema,
            InputType,
            RangedFloatParameterDescriptor,
            FloatRangeDescriptor,
            EnumParameterDescriptor,
            EnumVal,
        )

        schema = TaskSchema(
            inputs=[
                InputSchema(
                    key="input_dir",
                    label="Path to the directory containing the input images",
                    inputType=InputType.DIRECTORY,
                ),
                InputSchema(key="prompt", label="Prompt", inputType=InputType.TEXT),
            ],
            parameters=[
                ParameterSchema(
                    key="confidence",
                    label="Confidence",
                    value=RangedFloatParameterDescriptor(
                        range=FloatRangeDescriptor(min=0.0, max=1.0),
                        default=0.8,
                    ),
                ),
                ParameterSchema(
                    key="mode",
                    label="Processing Mode",
                    value=EnumParameterDescriptor(
                        enumVals=[
                            EnumVal(key="fast", value="fast", label="Fast"),
                            EnumVal(key="accurate", value="accurate", label="Accurate"),
                        ],
                        default="fast",
                    ),
                ),
            ],
        )
        d = tmp_path / "evidence"
        d.mkdir()
        (d / "kid.jpeg").write_bytes(b'\xff\xd8\xff\xd9')
        form_data = {
            'inputs': {'input_dir': {'path': str(d)}, 'prompt': {'text': 'x'}},
            'parameters': {'confidence': 0.8, 'mode': 'fast'},
        }
        result = validate_form_data(form_data, schema)
        assert result['is_valid'] is True

    def test_image_endpoint_skips_raster_check_for_output_dir(self, tmp_path):
        """Output folders are often empty until the job runs; do not require raster files there."""
        from rb.api.models import (
            TaskSchema,
            InputSchema,
            ParameterSchema,
            InputType,
            RangedFloatParameterDescriptor,
            FloatRangeDescriptor,
            EnumParameterDescriptor,
            EnumVal,
        )

        input_dir = tmp_path / "in"
        input_dir.mkdir()
        (input_dir / "pic.jpg").write_bytes(b"\xff\xd8\xff\xd9")
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        (output_dir / "readme.txt").write_text("no images here")

        schema = TaskSchema(
            inputs=[
                InputSchema(
                    key="input_dir",
                    label="Folder of images",
                    inputType=InputType.DIRECTORY,
                ),
                InputSchema(
                    key="output_dir",
                    label="Path to the directory for the output summaries",
                    inputType=InputType.DIRECTORY,
                ),
                InputSchema(key="prompt", label="Prompt", inputType=InputType.TEXT),
            ],
            parameters=[
                ParameterSchema(
                    key="confidence",
                    label="Confidence",
                    value=RangedFloatParameterDescriptor(
                        range=FloatRangeDescriptor(min=0.0, max=1.0),
                        default=0.8,
                    ),
                ),
                ParameterSchema(
                    key="mode",
                    label="Processing Mode",
                    value=EnumParameterDescriptor(
                        enumVals=[
                            EnumVal(key="fast", value="fast", label="Fast"),
                            EnumVal(key="accurate", value="accurate", label="Accurate"),
                        ],
                        default="fast",
                    ),
                ),
            ],
        )
        form_data = {
            "inputs": {
                "input_dir": {"path": str(input_dir)},
                "output_dir": {"path": str(output_dir)},
                "prompt": {"text": "captions"},
            },
            "parameters": {"confidence": 0.8, "mode": "fast"},
        }
        result = validate_form_data(form_data, schema)
        assert result["is_valid"] is True

    def test_text_summarization_paired_dirs_skip_raster_check(self, tmp_path):
        """input_dir + output_dir for text summary must not require image rasters."""
        from rb.api.models import (
            TaskSchema,
            InputSchema,
            ParameterSchema,
            InputType,
            EnumParameterDescriptor,
            EnumVal,
        )

        input_dir = tmp_path / "docs"
        input_dir.mkdir()
        (input_dir / "a.md").write_text("# hello")
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        schema = TaskSchema(
            inputs=[
                InputSchema(
                    key="input_dir",
                    label="Path to the directory containing the input files",
                    inputType=InputType.DIRECTORY,
                ),
                InputSchema(
                    key="output_dir",
                    label="Path to the directory containing the output files",
                    inputType=InputType.DIRECTORY,
                ),
            ],
            parameters=[
                ParameterSchema(
                    key="model",
                    label="Model",
                    value=EnumParameterDescriptor(
                        enumVals=[EnumVal(key="m", value="m", label="m")],
                        default="m",
                    ),
                )
            ],
        )
        form_data = {
            "inputs": {
                "input_dir": {"path": str(input_dir)},
                "output_dir": {"path": str(output_dir)},
            },
            "parameters": {"model": "m"},
        }
        assert validate_form_data(form_data, schema)["is_valid"] is True

    def test_audio_endpoint_skips_image_content_check(self, tmp_path):
        from rb.api.models import (
            TaskSchema,
            InputSchema,
            ParameterSchema,
            InputType,
            RangedFloatParameterDescriptor,
            FloatRangeDescriptor,
            EnumParameterDescriptor,
            EnumVal,
        )

        schema = TaskSchema(
            inputs=[
                InputSchema(
                    key="input_dir",
                    label="Provide audio files directory",
                    inputType=InputType.DIRECTORY,
                ),
                InputSchema(key="prompt", label="Prompt", inputType=InputType.TEXT),
            ],
            parameters=[
                ParameterSchema(
                    key="confidence",
                    label="Confidence",
                    value=RangedFloatParameterDescriptor(
                        range=FloatRangeDescriptor(min=0.0, max=1.0),
                        default=0.8,
                    ),
                ),
                ParameterSchema(
                    key="mode",
                    label="Processing Mode",
                    value=EnumParameterDescriptor(
                        enumVals=[
                            EnumVal(key="fast", value="fast", label="Fast"),
                            EnumVal(key="accurate", value="accurate", label="Accurate"),
                        ],
                        default="fast",
                    ),
                ),
            ],
        )
        d = tmp_path / "audio_in"
        d.mkdir()
        (d / "speech.txt").write_text('x')
        form_data = {
            'inputs': {'input_dir': {'path': str(d)}, 'prompt': {'text': 'x'}},
            'parameters': {'confidence': 0.8, 'mode': 'fast'},
        }
        result = validate_form_data(form_data, schema)
        assert result['is_valid'] is True

    def test_validate_invalid_schema_dict(self):
        """Test validation with invalid schema dictionary"""
        form_data = {'inputs': {}, 'parameters': {}}
        invalid_schema = {'inputs': 'invalid', 'parameters': []}
        
        result = validate_form_data(form_data, invalid_schema)
        
        assert result['is_valid'] is False
        assert 'schema' in result['errors']
    
    def test_validate_form_data_parameters_pass_through(self, sample_task_schema, temp_directory):
        """``validate_form_data`` does not range-check parameters against the task schema."""
        form_data = {
            "inputs": {
                "input_dir": {"path": str(temp_directory)},
                "prompt": {"text": "Test"},
            },
            "parameters": {
                "confidence": 1.5,
                "mode": "fast",
            },
        }

        result = validate_form_data(form_data, sample_task_schema)

        assert result["is_valid"] is True
        assert result["validated_data"].parameters["confidence"] == 1.5


class TestCreateInputModel:
    """Tests for _create_input_model function"""
    
    def test_create_directory_input(self, sample_task_schema):
        """Test creating DirectoryInput model"""
        input_schema = sample_task_schema.inputs[0]  # input_dir
        value = {'path': str(Path.cwd())}
        
        result = _create_input_model(input_schema, value)
        
        assert isinstance(result, DirectoryInput)
        assert result.path == Path.cwd()
    
    def test_create_file_input(self):
        """Test creating FileInput model"""
        from rb.api.models import FileInput, InputSchema, InputType
        
        input_schema = InputSchema(
            key='file',
            label='File',
            inputType=InputType.FILE
        )
        value = {'path': str(Path(__file__))}
        
        result = _create_input_model(input_schema, value)
        
        assert isinstance(result, FileInput)
        assert result.path == Path(__file__)
    
    def test_create_text_input(self):
        """Test creating TextInput model"""
        from rb.api.models import TextInput, InputSchema, InputType
        
        input_schema = InputSchema(
            key='text',
            label='Text',
            inputType=InputType.TEXT
        )
        value = {'text': 'Hello world'}
        
        result = _create_input_model(input_schema, value)
        
        assert isinstance(result, TextInput)
        assert result.text == 'Hello world'


class TestValidateParameterValue:
    """Tests for _validate_parameter_value function"""
    
    def test_validate_ranged_float_valid(self, sample_task_schema):
        """Test validation of valid ranged float parameter"""
        param_schema = sample_task_schema.parameters[0]  # confidence
        value = 0.75
        
        # Should not raise
        _validate_parameter_value(value, param_schema)
    
    def test_validate_ranged_float_out_of_range(self, sample_task_schema):
        """Test validation fails for out-of-range float"""
        param_schema = sample_task_schema.parameters[0]  # confidence
        value = 1.5  # Out of range [0.0, 1.0]
        
        with pytest.raises(ValueError, match='must be between'):
            _validate_parameter_value(value, param_schema)
    
    def test_validate_enum_valid(self, sample_task_schema):
        """Test validation of valid enum parameter"""
        param_schema = sample_task_schema.parameters[1]  # mode
        value = 'fast'
        
        # Should not raise
        _validate_parameter_value(value, param_schema)
    
    def test_validate_enum_invalid(self, sample_task_schema):
        """Test validation fails for invalid enum value"""
        param_schema = sample_task_schema.parameters[1]  # mode
        value = 'invalid_mode'
        
        with pytest.raises(ValueError, match='must be one of'):
            _validate_parameter_value(value, param_schema)


class TestValidateResponseBody:
    """Tests for validate_response_body function"""
    
    def test_validate_valid_response(self):
        """Test validation of valid response body"""
        from rb.api.models import FileResponse
        
        response_data = {
            'output_type': 'file',
            'file_type': 'img',
            'path': '/path/to/file.jpg',
            'title': 'Test File'
        }
        
        result = validate_response_body(response_data)

        assert isinstance(result, ResponseBody)
        result_rb = cast(ResponseBody, result)
        assert isinstance(result_rb.root, FileResponse)
    
    def test_validate_invalid_response(self):
        """Test validation fails for invalid response"""
        response_data = {
            'output_type': 'invalid_type'
        }
        
        result = validate_response_body(response_data)
        
        assert isinstance(result, dict)
        assert result['is_valid'] is False
        assert 'errors' in result