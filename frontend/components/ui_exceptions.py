"""Exception types commonly caught in defensive UI rendering."""

from pydantic import ValidationError

from frontend.utils.exceptions import UI_RENDER_ERRORS

SCHEMA_PARSE_ERRORS = (*UI_RENDER_ERRORS, ValidationError)

__all__ = ["SCHEMA_PARSE_ERRORS", "UI_RENDER_ERRORS"]
