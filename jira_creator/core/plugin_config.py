#!/usr/bin/env python
"""
Plugin configuration classes for the plugin system.

This module provides configuration classes that plugins can use to
declare their requirements and preferences.
"""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional


@dataclass
class FieldMapping:
    """
    Configuration for a JIRA field mapping.

    Attributes:
        env_var: Environment variable name containing the field ID
        default: Default field ID if environment variable not set
        required: Whether this field is required for plugin operation
        description: Human-readable description of the field's purpose
    """

    env_var: str
    default: Optional[str] = None
    required: bool = False
    description: str = ""


@dataclass
class DisplayConfig:
    """
    Configuration for how a plugin displays issue data.

    Attributes:
        columns: List of column names to display
        sort_by: Default column to sort by
        sort_order: Sort order ('asc' or 'desc')
        truncate_summary: Whether to truncate long summaries
        show_details: Whether to show detailed issue information
        format: Output format ('table', 'json', 'csv')
    """

    columns: List[str]
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    truncate_summary: bool = True
    show_details: bool = False
    format: str = "table"


@dataclass
class ValidationRule:
    """
    A validation rule for issue fields.

    Attributes:
        field: Field name to validate
        validator: Function that takes a value and returns True if valid
        error_message: Error message to display if validation fails
        required: Whether the field is required (cannot be None/empty)
        min_length: Minimum length for string fields
        max_length: Maximum length for string fields
        pattern: Regex pattern the value must match
    """

    field: str
    validator: Optional[Callable[[Any], bool]] = None
    error_message: str = ""
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None

    def validate(self, value: Any) -> tuple[bool, str]:  # pylint: disable=too-many-return-statements
        """
        Validate a value against this rule.

        Arguments:
            value: The value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required
        if self.required and (value is None or value == ""):
            return False, f"{self.field} is required"

        # Skip other checks if value is None/empty and not required
        if value is None or value == "":
            return True, ""

        # Check min length
        if self.min_length is not None and isinstance(value, str) and len(value) < self.min_length:
            return False, f"{self.field} must be at least {self.min_length} characters"

        # Check max length
        if self.max_length is not None and isinstance(value, str) and len(value) > self.max_length:
            return False, f"{self.field} must be at most {self.max_length} characters"

        # Check pattern
        if self.pattern is not None and isinstance(value, str):
            import re

            if not re.match(self.pattern, value):
                return False, self.error_message or f"{self.field} does not match required pattern"

        # Check custom validator
        if self.validator is not None:
            try:
                if not self.validator(value):
                    return False, self.error_message or f"{self.field} validation failed"
            except Exception as e:  # pylint: disable=broad-exception-caught
                return False, f"{self.field} validation error: {e}"

        return True, ""
