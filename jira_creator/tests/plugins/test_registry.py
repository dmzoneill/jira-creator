#!/usr/bin/env python
"""Tests for the plugin registry."""

from argparse import ArgumentParser
from pathlib import Path
from unittest.mock import Mock, patch

from jira_creator.plugins.base import JiraPlugin
from jira_creator.plugins.registry import PluginRegistry


class MockPlugin(JiraPlugin):
    """Mock plugin for testing."""

    command_name = "mock-command"
    help_text = "Mock command for testing"

    def register_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("test_arg")

    def execute(self, client, args):
        return True

    def rest_operation(self, client, **kwargs):
        return {}


class TestPluginRegistry:
    """Test cases for PluginRegistry."""

    def test_init(self):
        """Test registry initialization."""
        registry = PluginRegistry()
        assert registry._plugins == {}
        assert registry._plugin_classes == {}

    def test_manual_plugin_registration(self):
        """Test manually adding a plugin to the registry."""
        registry = PluginRegistry()
        plugin = MockPlugin()

        # Manually add plugin
        registry._plugins["mock-command"] = plugin
        registry._plugin_classes["mock-command"] = MockPlugin

        # Test retrieval
        assert registry.get_plugin("mock-command") == plugin
        assert registry.get_plugin_class("mock-command") == MockPlugin

        # Test with underscores (should convert to hyphens)
        assert registry.get_plugin("mock_command") == plugin

    def test_create_plugin_with_dependencies(self):
        """Test creating a plugin instance with dependency injection."""
        registry = PluginRegistry()
        registry._plugin_classes["mock-command"] = MockPlugin

        # Create plugin with dependencies
        plugin = registry.create_plugin("mock-command", test_dep="injected")
        assert plugin is not None
        assert plugin.get_dependency("test_dep") == "injected"

    def test_list_plugins(self):
        """Test listing all registered plugins."""
        registry = PluginRegistry()

        # Add multiple plugins
        registry._plugins["cmd-a"] = Mock()
        registry._plugins["cmd-b"] = Mock()
        registry._plugins["cmd-c"] = Mock()

        plugins = registry.list_plugins()
        assert plugins == ["cmd-a", "cmd-b", "cmd-c"]  # Should be sorted

    def test_register_all_with_subparsers(self):
        """Test registering all plugins with argument parser."""
        registry = PluginRegistry()
        plugin = MockPlugin()
        registry._plugins["mock-command"] = plugin

        # Mock subparsers
        mock_subparsers = Mock()
        mock_parser = Mock()
        mock_subparsers.add_parser.return_value = mock_parser

        registry.register_all(mock_subparsers)

        # Verify add_parser was called correctly
        mock_subparsers.add_parser.assert_called_once_with("mock-command", help="Mock command for testing")

        # Verify register_arguments was called
        assert mock_parser.add_argument.called

    def test_clear(self):
        """Test clearing the registry."""
        registry = PluginRegistry()
        registry._plugins["test"] = Mock()
        registry._plugin_classes["test"] = Mock

        registry.clear()

        assert registry._plugins == {}
        assert registry._plugin_classes == {}

    @patch("jira_creator.plugins.registry.Path")
    @patch("importlib.import_module")
    def test_discover_plugins_error_handling(self, mock_import, mock_path):
        """Test that discovery continues even if one plugin fails to load."""
        registry = PluginRegistry()

        # Mock Path to return a fake plugin file
        mock_path_instance = Mock()
        mock_path_instance.glob.return_value = [Path("/fake/test_plugin.py")]
        mock_path.return_value = mock_path_instance

        # Make import_module raise an exception
        mock_import.side_effect = ImportError("Test error")

        # This should not raise an exception
        registry.discover_plugins()

        # Registry should still be empty but no exception raised
        assert registry._plugins == {}
