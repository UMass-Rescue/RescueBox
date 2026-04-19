"""
Unit tests for form data validation functionality.

This module tests the validation system that ensures form data conforms
to task schema requirements, including parameter ranges, input types,
and data integrity checks.
"""

import pytest
from pathlib import Path
from pydantic import ValidationError
import sys

# Add backend models to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'src' / 'rb-api' / 'rb'))

from frontend.utils.validators import (
    validate_form_data,
    validate_request_body,
    validate_response_body,
    _create_input_model,
    _validate_parameter_value,
    _format_validation_error,
)
from typing import cast

# Import required backend models
from rb.api.models import (
    DirectoryInput,
    ResponseBody,
)


class TestValidateFormData:
    """Tests for validate_form_data function.

    This class tests the core form validation logic that ensures
    submitted form data matches the expected task schema structure
    and parameter constraints.
    """

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

    def test_image_endpoint_rejects_dir_without_image_files(self, sample_task_schema, tmp_path):
        """Image-style endpoints require at least one common raster file under input_dir."""
        d = tmp_path / "evidence"
        d.mkdir()
        (d / "notes.txt").write_text("no images")
        form_data = {
            'inputs': {'input_dir': {'path': str(d)}, 'prompt': {'text': 'captions'}},
            'parameters': {'confidence': 0.8, 'mode': 'fast'},
        }
        result = validate_form_data(
            form_data, sample_task_schema, endpoint='image_summary/summarize-images'
        )
        assert result['is_valid'] is False
        assert 'input_dir' in result['errors']
        assert 'image' in result['errors']['input_dir'].lower()

    def test_image_endpoint_accepts_dir_with_jpeg(self, sample_task_schema, tmp_path):
        d = tmp_path / "evidence"
        d.mkdir()
        (d / "kid.jpeg").write_bytes(b'\xff\xd8\xff\xd9')
        form_data = {
            'inputs': {'input_dir': {'path': str(d)}, 'prompt': {'text': 'x'}},
            'parameters': {'confidence': 0.8, 'mode': 'fast'},
        }
        result = validate_form_data(
            form_data, sample_task_schema, endpoint='image_summary/summarize-images'
        )
        assert result['is_valid'] is True

    def test_audio_endpoint_skips_image_content_check(self, sample_task_schema, tmp_path):
        d = tmp_path / "audio_in"
        d.mkdir()
        (d / "speech.txt").write_text('x')
        form_data = {
            'inputs': {'input_dir': {'path': str(d)}, 'prompt': {'text': 'x'}},
            'parameters': {'confidence': 0.8, 'mode': 'fast'},
        }
        result = validate_form_data(form_data, sample_task_schema, endpoint='audio/transcribe')
        assert result['is_valid'] is True

    def test_validate_invalid_schema_dict(self):
        """Test validation with invalid schema dictionary"""
        form_data = {'inputs': {}, 'parameters': {}}
        invalid_schema = {'inputs': 'invalid', 'parameters': []}
        
        result = validate_form_data(form_data, invalid_schema)
        
        assert result['is_valid'] is False
        assert 'schema' in result['errors']
    
    def test_validate_parameter_range(self, sample_task_schema, temp_directory):
        """Test parameter range validation.

        Ensures that parameters outside their valid ranges are properly
        detected and reported as validation errors.
        """
        form_data = {
            'inputs': {
                'input_dir': {'path': str(temp_directory)},
                'prompt': {'text': 'Test'}
            },
            'parameters': {
                'confidence': 1.5,  # Out of range (valid: 0.0-1.0)
                'mode': 'fast'
            }
        }
        
        result = validate_form_data(form_data, sample_task_schema)
        
        assert result['is_valid'] is False
        assert 'confidence' in result['errors']


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
        from rb.api.models import FileResponse, FileType
        
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