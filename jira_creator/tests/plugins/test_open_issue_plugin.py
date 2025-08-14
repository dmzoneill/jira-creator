#!/usr/bin/env python
"""Tests for the open issue plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import OpenIssueError
from jira_creator.plugins.open_issue_plugin import OpenIssuePlugin


class TestOpenIssuePlugin:
    """Test cases for OpenIssuePlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = OpenIssuePlugin()
        assert plugin.command_name == "open-issue"
        assert plugin.help_text == "Open a Jira issue in your web browser"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = OpenIssuePlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        mock_parser.add_argument.assert_called_once_with("issue_key", help="The Jira issue key (e.g., PROJ-123)")

    def test_rest_operation(self):
        """Test the REST operation returns empty dict."""
        plugin = OpenIssuePlugin()
        mock_client = Mock()

        result = plugin.rest_operation(mock_client)

        assert result == {}
        # Verify no client requests were made
        mock_client.request.assert_not_called()

    @patch("jira_creator.plugins.open_issue_plugin.subprocess.Popen")
    @patch("jira_creator.plugins.open_issue_plugin.sys.platform", "darwin")
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_success_macos(self, mock_env_fetcher, mock_popen):
        """Test successful execution on macOS."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        plugin = OpenIssuePlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        result = plugin.execute(mock_client, args)

        assert result is True
        mock_env_fetcher.get.assert_called_once_with("JIRA_URL")
        mock_popen.assert_called_once_with(["open", "https://jira.example.com/browse/TEST-123"])

    @patch("jira_creator.plugins.open_issue_plugin.subprocess.Popen")
    @patch("jira_creator.plugins.open_issue_plugin.sys.platform", "linux")
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_success_linux(self, mock_env_fetcher, mock_popen):
        """Test successful execution on Linux."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        plugin = OpenIssuePlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        result = plugin.execute(mock_client, args)

        assert result is True
        mock_popen.assert_called_once_with(["xdg-open", "https://jira.example.com/browse/TEST-123"])

    @patch("jira_creator.plugins.open_issue_plugin.subprocess.Popen")
    @patch("jira_creator.plugins.open_issue_plugin.sys.platform", "linux2")
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_success_linux2(self, mock_env_fetcher, mock_popen):
        """Test successful execution on Linux2."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        plugin = OpenIssuePlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        result = plugin.execute(mock_client, args)

        assert result is True
        mock_popen.assert_called_once_with(["xdg-open", "https://jira.example.com/browse/TEST-123"])

    @patch("jira_creator.plugins.open_issue_plugin.subprocess.Popen")
    @patch("jira_creator.plugins.open_issue_plugin.sys.platform", "win32")
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_success_windows(self, mock_env_fetcher, mock_popen):
        """Test successful execution on Windows."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        plugin = OpenIssuePlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        result = plugin.execute(mock_client, args)

        assert result is True
        mock_popen.assert_called_once_with(["start", "https://jira.example.com/browse/TEST-123"], shell=True)

    @patch("jira_creator.plugins.open_issue_plugin.subprocess.Popen")
    @patch("jira_creator.plugins.open_issue_plugin.sys.platform", "darwin")
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_success_prints_message(self, mock_env_fetcher, mock_popen, capsys):
        """Test that success message is printed."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        plugin = OpenIssuePlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "🌐 Opening https://jira.example.com/browse/TEST-123 in browser..." in captured.out

    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_failure_no_jira_url(self, mock_env_fetcher):
        """Test handling when JIRA_URL is not set."""
        mock_env_fetcher.get.return_value = None

        plugin = OpenIssuePlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(OpenIssueError) as exc_info:
            plugin.execute(mock_client, args)

        assert "JIRA_URL not set in environment" in str(exc_info.value)

    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_failure_no_jira_url_prints_message(self, mock_env_fetcher, capsys):
        """Test that error message is printed when JIRA_URL is not set."""
        mock_env_fetcher.get.return_value = None

        plugin = OpenIssuePlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(OpenIssueError):
            plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "❌ Failed to open issue: JIRA_URL not set in environment" in captured.out

    @patch("jira_creator.plugins.open_issue_plugin.sys.platform", "unsupported_os")
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_failure_unsupported_platform(self, mock_env_fetcher):
        """Test handling of unsupported platform."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        plugin = OpenIssuePlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(OpenIssueError) as exc_info:
            plugin.execute(mock_client, args)

        assert "Unsupported platform: unsupported_os" in str(exc_info.value)

    @patch("jira_creator.plugins.open_issue_plugin.sys.platform", "unsupported_os")
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_failure_unsupported_platform_prints_message(self, mock_env_fetcher, capsys):
        """Test that error message is printed for unsupported platform."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        plugin = OpenIssuePlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        with pytest.raises(OpenIssueError):
            plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "❌ Failed to open issue: Unsupported platform: unsupported_os" in captured.out

    @patch("jira_creator.plugins.open_issue_plugin.subprocess.Popen")
    @patch("jira_creator.plugins.open_issue_plugin.sys.platform", "darwin")
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_with_different_issue_keys(self, mock_env_fetcher, mock_popen):
        """Test execution with various issue key formats."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        plugin = OpenIssuePlugin()
        mock_client = Mock()

        # Test with different issue key formats
        test_cases = [
            "PROJ-123",
            "ABC-1",
            "LONGPROJECT-99999",
            "X-1234",
        ]

        for issue_key in test_cases:
            mock_popen.reset_mock()
            args = Namespace(issue_key=issue_key)

            result = plugin.execute(mock_client, args)

            assert result is True
            mock_popen.assert_called_once_with(["open", f"https://jira.example.com/browse/{issue_key}"])

    @patch("jira_creator.plugins.open_issue_plugin.subprocess.Popen")
    @patch("jira_creator.plugins.open_issue_plugin.sys.platform", "darwin")
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_with_different_jira_urls(self, mock_env_fetcher, mock_popen):
        """Test execution with various JIRA URL formats."""
        plugin = OpenIssuePlugin()
        mock_client = Mock()

        # Test with different JIRA URL formats
        test_cases = [
            "https://jira.company.com",
            "http://jira.local",
            "https://jira.company.com:8080",
            "https://company.atlassian.net",
        ]

        for jira_url in test_cases:
            mock_env_fetcher.get.return_value = jira_url
            mock_popen.reset_mock()
            args = Namespace(issue_key="TEST-123")

            result = plugin.execute(mock_client, args)

            assert result is True
            mock_popen.assert_called_once_with(["open", f"{jira_url}/browse/TEST-123"])

    @patch("jira_creator.plugins.open_issue_plugin.subprocess.Popen")
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_subprocess_error(self, mock_env_fetcher, mock_popen):
        """Test handling of subprocess errors."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"
        mock_popen.side_effect = OSError("Command not found")

        plugin = OpenIssuePlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123")

        # The plugin doesn't catch subprocess errors, so they propagate
        with pytest.raises(OSError):
            plugin.execute(mock_client, args)
