"""Tests for the setter base plugin."""

import inspect
from argparse import ArgumentParser, Namespace
from typing import Any
from unittest.mock import Mock

import pytest

from jira_creator.core.plugin_setter_base import SetterPlugin
from jira_creator.plugins.set_priority_plugin import SetPriorityError


class StubSetter(SetterPlugin):
    """Configurable SetterPlugin stub that records every REST call it receives."""

    def __init__(self, field: str, argument: str, result: dict[str, Any] | None = None) -> None:
        super().__init__()
        self._field = field
        self._argument = argument
        self._result = {} if result is None else result
        self.calls: list[tuple[Any, dict[str, Any]]] = []

    @property
    def field_name(self) -> str:
        """Return the configured field name."""
        return self._field

    @property
    def argument_name(self) -> str:
        """Return the configured argument name."""
        return self._argument

    def rest_operation(self, client: Any, **kwargs) -> dict[str, Any]:
        """Record the call and return the configured result."""
        self.calls.append((client, kwargs))
        return self._result


class FailingPrioritySetter(StubSetter):
    """Priority setter stub whose REST operation raises SetPriorityError."""

    def get_exception_class(self):
        """Return the priority-specific exception class."""
        return SetPriorityError

    def rest_operation(self, client: Any, **kwargs) -> dict[str, Any]:
        """Record the call, then fail like an invalid priority would."""
        self.calls.append((client, kwargs))
        raise SetPriorityError("Invalid priority")


class StoryPointsSetter(StubSetter):
    """Story points setter stub with a custom success message."""

    def format_success_message(self, issue_key: str, value: Any) -> str:
        """Return a story-points specific success message."""
        return f"✅ Story points for {issue_key} set to '{value}'"


class ExtraArgumentSetter(StubSetter):
    """Setter stub that registers one additional CLI argument."""

    def register_additional_arguments(self, parser: ArgumentParser) -> None:
        """Register the --extra argument."""
        parser.add_argument("--extra", help="Extra argument")


class TestSetterPlugin:
    """Test cases for SetterPlugin abstract base class."""

    def test_abstract_class_cannot_be_instantiated(self):
        """Test that SetterPlugin cannot be instantiated directly."""
        assert inspect.isabstract(SetterPlugin)
        assert SetterPlugin.__abstractmethods__ == {"field_name", "argument_name", "rest_operation"}

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
        plugin = StubSetter("test field", "test_value", {"success": True})

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
        plugin = StubSetter("priority", "priority")
        assert plugin.argument_help == "The priority to set"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = StubSetter("status", "status")
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
        plugin = StubSetter("component", "component")
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", component="Backend")

        result = plugin.execute(mock_client, args)

        assert result is True
        assert plugin.calls == [(mock_client, {"issue_key": "TEST-123", "value": "Backend", "args": args})]

    def test_execute_with_custom_exception(self):
        """Test execution with custom exception class."""
        plugin = FailingPrioritySetter("priority", "priority")
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", priority="Invalid")

        with pytest.raises(SetPriorityError):
            plugin.execute(mock_client, args)

    def test_format_success_message(self, capsys):
        """Test custom success message formatting."""
        plugin = StoryPointsSetter("story points", "points")
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", points=5)

        plugin.execute(mock_client, args)
        assert "✅ Story points for TEST-123 set to '5'" in capsys.readouterr().out

    def test_register_additional_arguments(self):
        """Test that register_additional_arguments is called."""
        plugin = ExtraArgumentSetter("custom", "custom_value")
        mock_parser = Mock(spec=ArgumentParser)

        plugin.register_arguments(mock_parser)

        # Verify additional argument was registered
        assert mock_parser.add_argument.call_count == 3
        calls = mock_parser.add_argument.call_args_list
        assert calls[2][0] == ("--extra",)
        assert calls[2][1]["help"] == "Extra argument"

    def test_stub_methods_coverage(self):
        """Test stub methods to improve coverage."""
        plugin1 = StubSetter("test field", "test_value", {"success": True})
        assert plugin1.rest_operation(None) == {"success": True}

        plugin2 = StubSetter("priority", "priority")
        result = plugin2.rest_operation(None)
        assert isinstance(result, dict) and not result
        assert plugin2.argument_name == "priority"

        plugin3 = ExtraArgumentSetter("component", "component")
        result = plugin3.rest_operation(None)
        assert isinstance(result, dict) and not result

        plugin5 = StubSetter("status", "status")
        result = plugin5.rest_operation(None)
        assert isinstance(result, dict) and not result
