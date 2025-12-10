#!/usr/bin/env python
"""Tests for the plugin registry."""

from argparse import ArgumentParser
from pathlib import Path
from unittest.mock import Mock, patch

from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.core.plugin_registry import PluginRegistry


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

    def test_mock_plugin_methods(self):
        """Test MockPlugin methods for coverage."""
        plugin = MockPlugin()

        # Test execute method
        result = plugin.execute(None, None)
        assert result is True

        # Test rest_operation method
        result = plugin.rest_operation(None)
        assert result == {}

    @patch("jira_creator.core.plugin_registry.Path")
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

    def test_create_plugin_nonexistent(self):
        """Test create_plugin returns None for nonexistent command - covers line 112."""
        registry = PluginRegistry()

        result = registry.create_plugin("nonexistent-command")

        assert result is None

    def test_get_all_plugin_names(self):
        """Test get_all_plugin_names method - covers line 132."""
        registry = PluginRegistry()

        # Add some plugins
        registry._plugins["cmd-a"] = Mock()
        registry._plugins["cmd-b"] = Mock()

        result = registry.get_all_plugin_names()

        assert result == ["cmd-a", "cmd-b"]

    @patch("jira_creator.core.plugin_registry.Path")
    def test_discover_plugins_with_custom_dir(self, mock_path):
        """Test discover_plugins with custom directory - covers line 42."""
        registry = PluginRegistry()

        mock_instance = Mock()
        mock_instance.glob.return_value = []
        mock_path.return_value = mock_instance

        # Call with custom path to trigger line 42
        registry.discover_plugins("/custom/plugin/path")

        # Verify Path was called with custom path
        mock_path.assert_called_with("/custom/plugin/path")

    @patch("jira_creator.core.plugin_registry.Path")
    def test_discover_plugins_skip_private_files(self, mock_path_class):
        """Test discover_plugins skips files starting with underscore - covers line 47."""
        registry = PluginRegistry()

        # Create mock files - one private, one public
        private_file = Mock()
        private_file.name = "_private_plugin.py"

        public_file = Mock()
        public_file.name = "public_plugin.py"
        public_file.stem = "public_plugin"

        # Mock Path to return both files
        mock_instance = Mock()
        mock_instance.glob.return_value = [private_file, public_file]
        mock_path_class.return_value = mock_instance

        with patch("importlib.import_module") as mock_import:
            # Set up a basic mock module
            mock_module = Mock()
            mock_import.return_value = mock_module

            with patch("inspect.getmembers", return_value=[]):
                registry.discover_plugins("/test/path")

                # Should only import the public plugin module (may be called multiple times for inspect, etc.)
                # Check that public_plugin was imported but _private_plugin was not
                import_calls = [str(call) for call in mock_import.call_args_list]
                assert any("public_plugin" in call for call in import_calls)
                assert not any("_private_plugin" in call for call in import_calls)

    @patch("jira_creator.core.plugin_registry.inspect.getmembers")
    @patch("jira_creator.core.plugin_registry.inspect.isabstract")
    @patch("jira_creator.core.plugin_registry.importlib.import_module")
    def test_reload_plugin_from_file_success(self, mock_import, mock_isabstract, mock_getmembers):
        """Test reload_plugin_from_file with successful reload - covers lines 163-191."""
        registry = PluginRegistry()

        # Mock the plugin class
        mock_plugin_class = type(
            "TestPlugin",
            (JiraPlugin,),
            {
                "command_name": "test",
                "help_text": "Test plugin",
                "register_arguments": lambda self, p: None,
                "execute": lambda self, c, a: True,
                "rest_operation": lambda self, c, **kw: {},
            },
        )

        mock_module = Mock()
        mock_import.return_value = mock_module
        mock_getmembers.return_value = [("TestPlugin", mock_plugin_class)]
        mock_isabstract.return_value = False

        # Create a real temp file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix="_plugin.py", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result = registry.reload_plugin_from_file(tmp_path)
            assert result is True
        finally:
            Path(tmp_path).unlink()

    @patch("jira_creator.core.plugin_registry.inspect.getmembers")
    @patch("jira_creator.core.plugin_registry.inspect.isabstract")
    @patch("jira_creator.core.plugin_registry.importlib.reload")
    def test_reload_plugin_from_file_module_already_loaded(self, mock_reload, mock_isabstract, mock_getmembers):
        """Test reload_plugin_from_file when module already in sys.modules - covers line 176."""
        import sys
        import tempfile

        registry = PluginRegistry()

        # Create a real temp file
        with tempfile.NamedTemporaryFile(suffix="_plugin.py", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Get the module name from the file
            module_name = f"jira_creator.plugins.{Path(tmp_path).stem}"

            # Add module to sys.modules
            mock_module = Mock()
            sys.modules[module_name] = mock_module

            mock_reload.return_value = mock_module

            # Mock the plugin class
            mock_plugin_class = type(
                "TestPlugin",
                (JiraPlugin,),
                {
                    "command_name": "test",
                    "help_text": "Test plugin",
                    "register_arguments": lambda self, p: None,
                    "execute": lambda self, c, a: True,
                    "rest_operation": lambda self, c, **kw: {},
                },
            )

            mock_getmembers.return_value = [("TestPlugin", mock_plugin_class)]
            mock_isabstract.return_value = False

            result = registry.reload_plugin_from_file(tmp_path)

            assert result is True
            mock_reload.assert_called_once()

            # Clean up
            if module_name in sys.modules:
                del sys.modules[module_name]
        finally:
            Path(tmp_path).unlink()

    def test_reload_plugin_from_file_invalid_path(self):
        """Test reload_plugin_from_file with invalid path - covers line 169."""
        registry = PluginRegistry()

        # File doesn't exist
        result = registry.reload_plugin_from_file("/nonexistent/file.py")

        assert result is False

    def test_reload_plugin_from_file_not_plugin_file(self):
        """Test reload_plugin_from_file with non-plugin file - covers line 169."""
        import tempfile

        registry = PluginRegistry()

        # File exists but doesn't end with _plugin.py
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            result = registry.reload_plugin_from_file(tmp_path)
            assert result is False
        finally:
            Path(tmp_path).unlink()

    @patch("jira_creator.core.plugin_registry.importlib.import_module")
    def test_reload_plugin_from_file_exception(self, mock_import):
        """Test reload_plugin_from_file with exception - covers lines 193-195."""
        import tempfile

        registry = PluginRegistry()

        # Create a real temp file with proper name
        with tempfile.NamedTemporaryFile(suffix="_plugin.py", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            mock_import.side_effect = ImportError("Test error")
            result = registry.reload_plugin_from_file(tmp_path)
            assert result is False
        finally:
            Path(tmp_path).unlink()
