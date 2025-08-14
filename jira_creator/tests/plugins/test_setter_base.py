#!/usr/bin/env python
"""Tests for the setter base plugin."""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import SetPriorityError
from jira_creator.plugins.setter_base import SetterPlugin


class TestSetterPlugin:
    """Test cases for SetterPlugin abstract base class."""

    def test_abstract_class_cannot_be_instantiated(self):
        """Test that SetterPlugin cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SetterPlugin()

    def test_abstract_methods_coverage(self):
        """Test to cover the abstract method pass statements."""
        # This test ensures the abstract methods are covered
        # by calling them directly on the class (not instance)

        # These will just return None/pass but will be covered
        assert SetterPlugin.field_name.fget(None) is None  # Line 28
        assert SetterPlugin.argument_name.fget(None) is None  # Line 34
        assert SetterPlugin.rest_operation(None, None) is None  # Line 133

    def test_concrete_implementation(self):
        """Test a concrete implementation of SetterPlugin."""

        class TestSetterPlugin(SetterPlugin):
            """Test implementation of SetterPlugin."""

            @property
            def field_name(self) -> str:
                return "test field"

            @property
            def argument_name(self) -> str:
                return "test_value"

            def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
                return {"success": True}

        # Test the concrete implementation
        plugin = TestSetterPlugin()

        # Test properties
        assert plugin.field_name == "test field"
        assert plugin.argument_name == "test_value"
        assert plugin.argument_help == "The test field to set"
        assert plugin.command_name == "set-test-field"
        assert plugin.help_text == "Set the test field of a Jira issue"

        # Test get_exception_class
        assert plugin.get_exception_class() == Exception

    def test_argument_help_property(self):
        """Test the argument_help property default implementation."""

        class TestPlugin(SetterPlugin):
            @property
            def field_name(self) -> str:
                return "priority"

            @property
            def argument_name(self) -> str:
                return "priority"

            def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
                return {}

        plugin = TestPlugin()
        assert plugin.argument_help == "The priority to set"

    def test_register_arguments(self):
        """Test argument registration."""

        class TestPlugin(SetterPlugin):
            @property
            def field_name(self) -> str:
                return "status"

            @property
            def argument_name(self) -> str:
                return "status"

            def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
                return {}

        plugin = TestPlugin()
        mock_parser = Mock(spec=ArgumentParser)

        plugin.register_arguments(mock_parser)

        # Verify arguments were registered
        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list

        # First argument: issue_key
        assert calls[0][0] == ("issue_key",)
        assert calls[0][1]["help"] == "The Jira issue key (e.g., PROJ-123)"

        # Second argument: status
        assert calls[1][0] == ("status",)
        assert calls[1][1]["help"] == "The status to set"

    def test_execute_success(self):
        """Test successful execution."""

        class TestPlugin(SetterPlugin):
            @property
            def field_name(self) -> str:
                return "component"

            @property
            def argument_name(self) -> str:
                return "component"

            def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
                return {"key": kwargs["issue_key"]}

        plugin = TestPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", component="Backend")

        result = plugin.execute(mock_client, args)

        assert result is True

    def test_execute_with_custom_exception(self):
        """Test execution with custom exception class."""

        class TestPlugin(SetterPlugin):
            @property
            def field_name(self) -> str:
                return "priority"

            @property
            def argument_name(self) -> str:
                return "priority"

            def get_exception_class(self):
                return SetPriorityError

            def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
                raise SetPriorityError("Invalid priority")

        plugin = TestPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", priority="Invalid")

        with pytest.raises(SetPriorityError):
            plugin.execute(mock_client, args)

    def test_format_success_message(self):
        """Test custom success message formatting."""

        class TestPlugin(SetterPlugin):
            @property
            def field_name(self) -> str:
                return "story points"

            @property
            def argument_name(self) -> str:
                return "points"

            def format_success_message(self, issue_key: str, value: Any) -> str:
                return f"✅ Story points set to '{value}'"

            def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
                return {}

        plugin = TestPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", points=5)

        # Capture print output
        import io
        import sys

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            plugin.execute(mock_client, args)
            output = captured_output.getvalue()
            assert "✅ Story points set to '5'" in output
        finally:
            sys.stdout = sys.__stdout__

    def test_register_additional_arguments(self):
        """Test that register_additional_arguments is called."""

        class TestPlugin(SetterPlugin):
            @property
            def field_name(self) -> str:
                return "custom"

            @property
            def argument_name(self) -> str:
                return "custom_value"

            def register_additional_arguments(self, parser: ArgumentParser) -> None:
                parser.add_argument("--extra", help="Extra argument")

            def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
                return {}

        plugin = TestPlugin()
        mock_parser = Mock(spec=ArgumentParser)

        plugin.register_arguments(mock_parser)

        # Verify additional argument was registered
        assert mock_parser.add_argument.call_count == 3
        calls = mock_parser.add_argument.call_args_list
        assert calls[2][0] == ("--extra",)
        assert calls[2][1]["help"] == "Extra argument"
