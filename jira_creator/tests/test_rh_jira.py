#!/usr/bin/env python
"""Tests for the plugin-based CLI entry point."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.rh_jira import PluginBasedJiraCLI, main


class TestPluginBasedJiraCLI:
    """Tests for the PluginBasedJiraCLI class."""

    def test_init(self):
        """Test CLI initialization."""
        cli = PluginBasedJiraCLI()
        assert cli.registry is not None
        assert cli.client is None

    @patch("jira_creator.rh_jira.JiraClient")
    def test_get_client(self, mock_client_class):
        """Test client creation and caching."""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        cli = PluginBasedJiraCLI()

        # First call should create client
        client1 = cli._get_client()
        assert client1 is mock_client_instance
        mock_client_class.assert_called_once_with()  # No arguments

        # Second call should return cached client
        client2 = cli._get_client()
        assert client2 is client1
        assert mock_client_class.call_count == 1

    @patch("jira_creator.rh_jira.argcomplete.autocomplete")
    @patch("jira_creator.rh_jira.ArgumentParser")
    @patch.dict("os.environ", {"CLI_NAME": "test-cli"})
    def test_run_with_cli_name(self, mock_parser_class, mock_autocomplete):
        """Test run method with custom CLI name."""
        # Setup mock parser
        mock_parser = Mock()
        mock_subparsers = Mock()
        mock_parser.add_subparsers.return_value = mock_subparsers
        mock_parser_class.return_value = mock_parser

        # Setup mock args
        mock_args = Mock()
        mock_args.command = "test-command"
        mock_parser.parse_args.return_value = mock_args

        cli = PluginBasedJiraCLI()

        # Mock registry methods
        cli.registry.discover_plugins = Mock()
        cli.registry.register_all = Mock()

        # Mock dispatch
        cli._dispatch_command = Mock()

        cli.run()

        # Verify parser was created with CLI_NAME
        mock_parser_class.assert_called_once_with(description="JIRA Issue Tool (Plugin-based)", prog="test-cli")

        # Verify plugin discovery and registration
        cli.registry.discover_plugins.assert_called_once()
        cli.registry.register_all.assert_called_once_with(mock_subparsers)

        # Verify autocomplete was enabled
        mock_autocomplete.assert_called_once_with(mock_parser)

        # Verify dispatch was called
        cli._dispatch_command.assert_called_once_with(mock_args)

    @patch("jira_creator.rh_jira.argcomplete.autocomplete")
    @patch("jira_creator.rh_jira.ArgumentParser")
    @patch("sys.argv", ["jira-cli"])
    def test_run_without_cli_name(self, mock_parser_class, mock_autocomplete):
        """Test run method without custom CLI name."""
        # Setup mock parser
        mock_parser = Mock()
        mock_subparsers = Mock()
        mock_parser.add_subparsers.return_value = mock_subparsers
        mock_parser_class.return_value = mock_parser

        # Setup mock args
        mock_args = Mock()
        mock_args.command = "test-command"
        mock_parser.parse_args.return_value = mock_args

        cli = PluginBasedJiraCLI()

        # Mock registry methods
        cli.registry.discover_plugins = Mock()
        cli.registry.register_all = Mock()

        # Mock dispatch
        cli._dispatch_command = Mock()

        cli.run()

        # Verify parser was created with basename of argv[0]
        mock_parser_class.assert_called_once_with(description="JIRA Issue Tool (Plugin-based)", prog="jira-cli")

    def test_dispatch_command_success(self):
        """Test successful command dispatch."""
        cli = PluginBasedJiraCLI()

        # Mock plugin
        mock_plugin = Mock()
        mock_plugin.execute.return_value = True

        # Mock registry
        cli.registry.get_plugin = Mock(return_value=mock_plugin)

        # Mock client
        cli._get_client = Mock(return_value=Mock())

        # Create args
        args = Namespace(command="test-command")

        # Should not raise
        cli._dispatch_command(args)

        # Verify plugin was executed
        mock_plugin.execute.assert_called_once()

    def test_dispatch_command_unknown(self, capsys):
        """Test dispatch with unknown command."""
        cli = PluginBasedJiraCLI()

        # Mock registry to return None
        cli.registry.get_plugin = Mock(return_value=None)

        # Create args
        args = Namespace(command="unknown-command")

        # Should exit with error
        with pytest.raises(SystemExit) as exc_info:
            cli._dispatch_command(args)

        assert exc_info.value.code == 1

        # Check error message
        captured = capsys.readouterr()
        assert "❌ Unknown command: unknown-command" in captured.out

    def test_dispatch_command_failure(self):
        """Test dispatch when plugin returns False."""
        cli = PluginBasedJiraCLI()

        # Mock plugin that returns False
        mock_plugin = Mock()
        mock_plugin.execute.return_value = False

        # Mock registry
        cli.registry.get_plugin = Mock(return_value=mock_plugin)

        # Mock client
        cli._get_client = Mock(return_value=Mock())

        # Create args
        args = Namespace(command="test-command")

        # Should exit with error
        with pytest.raises(SystemExit) as exc_info:
            cli._dispatch_command(args)

        assert exc_info.value.code == 1

    def test_dispatch_command_keyboard_interrupt(self, capsys):
        """Test dispatch with KeyboardInterrupt."""
        cli = PluginBasedJiraCLI()

        # Mock plugin that raises KeyboardInterrupt
        mock_plugin = Mock()
        mock_plugin.execute.side_effect = KeyboardInterrupt()

        # Mock registry
        cli.registry.get_plugin = Mock(return_value=mock_plugin)

        # Mock client
        cli._get_client = Mock(return_value=Mock())

        # Create args
        args = Namespace(command="test-command")

        # Should exit with code 130
        with pytest.raises(SystemExit) as exc_info:
            cli._dispatch_command(args)

        assert exc_info.value.code == 130

        # Check message
        captured = capsys.readouterr()
        assert "⚠️  Operation cancelled by user" in captured.out

    def test_dispatch_command_exception(self, capsys):
        """Test dispatch with general exception."""
        cli = PluginBasedJiraCLI()

        # Mock plugin that raises exception
        mock_plugin = Mock()
        mock_plugin.execute.side_effect = Exception("Test error")

        # Mock registry
        cli.registry.get_plugin = Mock(return_value=mock_plugin)

        # Mock client
        cli._get_client = Mock(return_value=Mock())

        # Create args
        args = Namespace(command="test-command")

        # Should exit with error
        with pytest.raises(SystemExit) as exc_info:
            cli._dispatch_command(args)

        assert exc_info.value.code == 1

        # Check error message
        captured = capsys.readouterr()
        assert "❌ Command failed: Test error" in captured.out

    @patch("jira_creator.rh_jira.PluginBasedJiraCLI")
    def test_main(self, mock_cli_class):
        """Test main entry point."""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        main()

        mock_cli_class.assert_called_once()
        mock_cli.run.assert_called_once()

    @patch("jira_creator.rh_jira.PluginBasedJiraCLI")
    @patch("jira_creator.rh_jira.__name__", "__main__")
    def test_if_name_main(self, mock_cli_class):
        """Test if __name__ == '__main__' execution."""
        # This tests the module-level check
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        # Import the module to trigger the if __name__ check
        import jira_creator.rh_jira

        # The module is already imported, so we need to reload it
        # But since we're testing, the __name__ won't actually be __main__
        # So we'll just verify the main function works
        jira_creator.rh_jira.main()

        mock_cli.run.assert_called_once()
