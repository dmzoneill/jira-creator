#!/usr/bin/env python
"""
Tests specifically designed to improve code coverage to 100%.
"""

from argparse import ArgumentParser
from unittest.mock import Mock, mock_open, patch

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.plugins.add_comment_plugin import AddCommentPlugin
from jira_creator.plugins.base import JiraPlugin
from jira_creator.plugins.registry import PluginRegistry
from jira_creator.plugins.set_priority_plugin import SetPriorityPlugin
from jira_creator.rest.client import JiraClient
from jira_creator.templates.template_loader import TemplateLoader


class MockValidPlugin(JiraPlugin):
    """A valid plugin for testing registry."""

    @property
    def command_name(self):
        return "test-plugin"

    @property
    def help_text(self):
        return "Test plugin"

    def register_arguments(self, parser):
        return None

    def execute(self, client, args):
        return True

    def rest_operation(self, client, **kwargs):
        return {}


class TestCoverageImprovements:
    """Tests to achieve 100% code coverage."""

    def test_env_fetcher_empty_affects_version(self):
        """Test env_fetcher.py line 101: JIRA_AFFECTS_VERSION empty string handling."""
        with (
            patch.dict("os.environ", {"JIRA_AFFECTS_VERSION": ""}),
            patch.dict("sys.modules", {}, clear=True),  # Simulate non-pytest environment
        ):
            result = EnvFetcher.get("JIRA_AFFECTS_VERSION")
            assert result == ""

    def test_add_comment_plugin_register_arguments(self):
        """Test add_comment_plugin.py lines 37-41: register_arguments method."""
        plugin = AddCommentPlugin()
        parser = Mock(spec=ArgumentParser)

        plugin.register_arguments(parser)

        # Verify all arguments were added
        assert parser.add_argument.call_count == 3
        parser.add_argument.assert_any_call("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument.assert_any_call("-t", "--text", help="Comment text (if not provided, opens editor)")
        parser.add_argument.assert_any_call("--no-ai", action="store_true", help="Skip AI text improvement")

    def test_set_priority_plugin_register_arguments(self):
        """Test set_priority_plugin.py lines 39-40: register_arguments method."""
        plugin = SetPriorityPlugin()
        parser = Mock(spec=ArgumentParser)

        plugin.register_arguments(parser)

        # Verify arguments were added
        assert parser.add_argument.call_count >= 2
        parser.add_argument.assert_any_call("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def test_rest_client_debug_curl_generation(self):
        """Test client.py line 146: debug curl command generation."""
        # Mock environment variables needed for JiraClient initialization
        with patch.dict(
            "jira_creator.core.env_fetcher.EnvFetcher.vars",
            {
                "JIRA_URL": "http://test.com",
                "JIRA_PROJECT_KEY": "TEST",
                "JIRA_JPAT": "token123",
            },
        ):
            client = JiraClient()

            with patch.object(client, "generate_curl_command") as mock_curl:
                # Call request with debug=True to trigger curl generation
                with patch("requests.request") as mock_request:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.text = '{"result": "success"}'
                    mock_response.json.return_value = {"result": "success"}
                    mock_request.return_value = mock_response

                    client.request("GET", "/test", debug=True)

                    # Verify curl command was generated
                    mock_curl.assert_called_once()

    def test_template_loader_get_fields_return(self):
        """Test template_loader.py line 100: get_fields return statement."""
        # Mock the template file with correct format
        template_content = "FIELD|test_field\nFIELD|another_field\nTEMPLATE|\nThis is a template"
        with patch("builtins.open", mock_open(read_data=template_content)):
            with patch("os.path.exists", return_value=True):
                loader = TemplateLoader("task")

                result = loader.get_fields()

                # Should return the fields list extracted from template
                assert isinstance(result, list)
                assert "test_field" in result
                assert "another_field" in result

    def test_plugin_registry_custom_plugin_dir(self):
        """Test registry.py line 43: custom plugin_dir path conversion."""
        registry = PluginRegistry()

        with patch("jira_creator.plugins.registry.Path") as mock_path:
            mock_instance = Mock()
            mock_instance.glob.return_value = []
            mock_path.return_value = mock_instance

            # Call with custom path to trigger line 43
            registry.discover_plugins("/custom/plugin/path")

            # Verify Path was called with custom path
            mock_path.assert_called_with("/custom/plugin/path")

    def test_plugin_registry_skip_private_files(self):
        """Test registry.py line 48: skip private files."""
        registry = PluginRegistry()

        # Create mock files - one private, one public
        private_file = Mock()
        private_file.name = "_private_plugin.py"

        public_file = Mock()
        public_file.name = "public_plugin.py"
        public_file.stem = "public_plugin"

        with patch("jira_creator.plugins.registry.Path") as mock_path_class:
            # Mock the file path resolution
            mock_file_path = Mock()
            mock_parent = Mock()
            mock_parent.glob.return_value = [private_file, public_file]
            mock_file_path.parent = mock_parent
            mock_path_class.return_value = mock_file_path

            with patch("jira_creator.plugins.registry.importlib.import_module") as mock_import:
                # Set up a basic mock module to avoid further errors
                mock_module = Mock()
                mock_import.return_value = mock_module

                with patch("jira_creator.plugins.registry.inspect.getmembers") as mock_members:
                    mock_members.return_value = []

                    registry.discover_plugins()

                    # Should only import the public plugin, not the private one
                    mock_import.assert_called_with("jira_creator.plugins.public_plugin")

    def test_plugin_instance_creation_and_registration(self):
        """Test basic plugin functionality for coverage."""
        # Create a plugin instance to ensure constructor works
        plugin = MockValidPlugin()
        assert plugin.command_name == "test-plugin"
        assert plugin.help_text == "Test plugin"

        # Test registry methods
        registry = PluginRegistry()
        registry._plugins["test-plugin"] = plugin
        registry._plugin_classes["test-plugin"] = MockValidPlugin

        # Test that plugin can be retrieved
        assert registry.get_plugin("test-plugin") is plugin

    def test_plugin_registry_create_plugin_none_return(self):
        """Test registry.py line 113: create_plugin returns None for unknown command."""
        registry = PluginRegistry()

        result = registry.create_plugin("nonexistent-command")

        assert result is None
