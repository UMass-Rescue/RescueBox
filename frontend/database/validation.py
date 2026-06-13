"""
Database Validation and Serialization

This module provides utilities for validating and serializing data
used in database operations, including Pydantic model handling and
JSON serialization/deserialization.
"""

import json
import logging
from typing import Any, Dict, Optional, Union, Type, TypeVar
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class DatabaseValidator:
    """Utilities for database data validation and serialization."""

    @staticmethod
    def pydantic_to_dict(model: Union[BaseModel, Dict, Any]) -> Dict[str, Any]:
        """
        Convert Pydantic model, dict, or other object to dictionary.

        Args:
            model: Pydantic model, dict, or other object

        Returns:
            Dictionary representation
        """
        if hasattr(model, "model_dump"):
            # Pydantic v2
            return model.model_dump()
        elif hasattr(model, "__dict__"):
            # Object with __dict__
            return dict(model)
        elif isinstance(model, dict):
            # Already a dict
            return model
        else:
            # Fallback: convert to string and wrap
            return {"value": str(model)}

    @staticmethod
    def dict_to_pydantic(data: Union[Dict, Any], model_class: Type[T]) -> T:
        """
        Convert dictionary or other data to Pydantic model.

        Args:
            data: Dictionary or other data to convert
            model_class: Pydantic model class

        Returns:
            Instance of the Pydantic model

        Raises:
            ValidationError: If data doesn't match model schema
        """
        if isinstance(data, dict):
            try:
                return model_class(**data)
            except ValidationError:
                logger.error(
                    "Failed to validate %s from data: %s",
                    model_class.__name__,
                    data,
                )
                raise
        else:
            # Try to wrap non-dict data
            logger.warning(
                "Converting non-dict data to %s: %s",
                model_class.__name__,
                data,
            )
            return model_class(**{"value": data})

    @staticmethod
    def serialize_json(data: Any) -> str:
        """
        Serialize data to JSON string for database storage.

        Args:
            data: Data to serialize

        Returns:
            JSON string representation
        """
        try:
            # Convert Pydantic models to dict first
            if (
                hasattr(data, "model_dump")
                or hasattr(data, "__dict__")
                or isinstance(data, dict)
            ):
                serializable_data = DatabaseValidator.pydantic_to_dict(data)
            else:
                serializable_data = data

            return json.dumps(serializable_data, default=str, ensure_ascii=False)
        except (TypeError, ValueError):
            logger.error("Failed to serialize data to JSON: %s", data)
            raise

    @staticmethod
    def deserialize_json(
        json_str: str, model_class: Optional[Type[T]] = None
    ) -> Union[T, Dict, Any]:
        """
        Deserialize JSON string from database storage.

        Args:
            json_str: JSON string to deserialize
            model_class: Optional Pydantic model class to convert to

        Returns:
            Deserialized data, optionally converted to Pydantic model
        """
        try:
            data = json.loads(json_str)

            if model_class is not None:
                return DatabaseValidator.dict_to_pydantic(data, model_class)
            else:
                return data

        except (json.JSONDecodeError, ValidationError):
            logger.error("Failed to deserialize JSON: %s", json_str)
            raise

    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
        """
        Validate that required fields are present in data.

        Args:
            data: Dictionary to validate
            required_fields: List of required field names

        Raises:
            ValueError: If any required fields are missing
        """
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string value for database storage.

        Args:
            value: String to sanitize
            max_length: Optional maximum length

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)

        # Remove null bytes and other problematic characters
        value = value.replace("\x00", "")

        if max_length and len(value) > max_length:
            logger.warning(
                "Truncating string from %d to %d characters",
                len(value),
                max_length,
            )
            value = value[:max_length]

        return value

    @staticmethod
    def validate_status_enum(value: str, valid_values: list) -> str:
        """
        Validate that a status value is in the allowed set.

        Args:
            value: Status value to validate
            valid_values: List of valid status values

        Returns:
            Validated status value

        Raises:
            ValueError: If status is not valid
        """
        if value not in valid_values:
            raise ValueError(
                f"Invalid status '{value}'. Must be one of: {valid_values}"
            )
        return value
