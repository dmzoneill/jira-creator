#!/usr/bin/env python
"""Tests for the base plugin class."""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

import pytest

from jira_creator.plugins.base import JiraPlugin


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
