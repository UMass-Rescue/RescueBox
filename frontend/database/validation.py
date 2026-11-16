"""
Database Validation and Serialization

This module provides utilities for validating and serializing data
used in database operations, including Pydantic model handling and
JSON serialization/deserialization.
"""

import json
import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DatabaseValidator:
    """Utilities for database data validation and serialization."""

    @staticmethod
    def pydantic_to_dict(model: BaseModel | dict[str, Any] | Any) -> dict[str, Any]:
        """
        Convert Pydantic model, dict, or other object to dictionary.

        Args:
            model: Pydantic model, dict, or other object

        Returns:
            Dictionary representation
        """
        if isinstance(model, BaseModel):
            # Pydantic v2
            return model.model_dump()
        elif isinstance(model, dict):
            # Already a dict
            return model
        elif hasattr(model, "model_dump") and callable(getattr(model, "model_dump")):
            # Duck-typed object with model_dump method
            return getattr(model, "model_dump")()
        elif hasattr(model, "__dict__"):
            # Object with __dict__
            return dict(vars(model))
        else:
            # Fallback: convert to string and wrap
            return {"value": str(model)}

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
