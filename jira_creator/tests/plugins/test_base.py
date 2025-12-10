#!/usr/bin/env python
"""Tests for the base plugin class."""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

import pytest

from jira_creator.core.plugin_base import JiraPlugin


class MockPlugin(JiraPlugin):
    """Mock plugin for testing base functionality."""

    command_name = "test-command"
    help_text = "Test command"

    def register_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("test_arg")

    def execute(self, client: Any, args: Namespace) -> bool:
        return True

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        return {"status": "success"}


class TestJiraPlugin:
    """Test cases for JiraPlugin base class."""

    def test_plugin_properties(self):
        """Test that plugin properties work correctly."""
        plugin = MockPlugin()
        assert plugin.command_name == "test-command"
        assert plugin.help_text == "Test command"

    def test_dependency_injection(self):
        """Test dependency injection mechanism."""
        mock_dep = "injected_value"
        plugin = MockPlugin(test_dep=mock_dep)

        # Test getting injected dependency
        assert plugin.get_dependency("test_dep") == mock_dep

        # Test getting non-injected dependency with default
        assert plugin.get_dependency("missing_dep", "default") == "default"

        # Test callable default
        def default_factory():
            return "factory_value"

        assert plugin.get_dependency("missing_dep", default_factory) == "factory_value"

    def test_abstract_methods_required(self):
        """Test that abstract methods must be implemented."""
        with pytest.raises(TypeError):
            # This should fail because abstract methods aren't implemented
            class IncompletePlugin(JiraPlugin):
                pass

            IncompletePlugin()

    def test_mock_plugin_methods(self):
        """Test MockPlugin methods for coverage."""
        plugin = MockPlugin()

        # Test register_arguments
        from argparse import ArgumentParser

        parser = ArgumentParser()
        plugin.register_arguments(parser)
        # Verify the argument was added
        assert "test_arg" in [action.dest for action in parser._actions]

        # Test execute
        result = plugin.execute(None, None)
        assert result is True

        # Test rest_operation
        result = plugin.rest_operation(None)
        assert result == {"status": "success"}

    def test_set_dependency_method(self):
        """Test set_dependency method - covers line 111."""
        plugin = MockPlugin()

        # Set a dependency after initialization
        plugin.set_dependency("new_dep", "new_value")

        # Verify it was set
        assert plugin.get_dependency("new_dep") == "new_value"

    def test_get_fix_capabilities_default(self):
        """Test get_fix_capabilities returns empty list by default - covers line 166."""
        plugin = MockPlugin()

        # Default implementation should return empty list
        capabilities = plugin.get_fix_capabilities()
        assert capabilities == []
        assert isinstance(capabilities, list)

    def test_execute_fix_not_implemented(self):
        """Test execute_fix raises NotImplementedError by default - covers line 186."""
        plugin = MockPlugin()

        # Should raise NotImplementedError since MockPlugin doesn't implement it
        with pytest.raises(NotImplementedError) as exc_info:
            plugin.execute_fix(None, "some_method", {})

        assert "test-command" in str(exc_info.value)
        assert "some_method" in str(exc_info.value)
