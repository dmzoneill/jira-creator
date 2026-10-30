#!/usr/bin/env python
"""Tests for the open issue plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.plugins.open_issue_plugin import OpenIssueError, OpenIssuePlugin


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

    @patch("jira_creator.plugins.open_issue_plugin.webbrowser.open", return_value=True)
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_success(self, mock_env_fetcher, mock_open):
        """Test successful execution opens the default browser."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        result = OpenIssuePlugin().execute(Mock(), Namespace(issue_key="TEST-123"))

        assert result is True
        mock_env_fetcher.get.assert_called_once_with("JIRA_URL")
        mock_open.assert_called_once_with("https://jira.example.com/browse/TEST-123")

    @patch("jira_creator.plugins.open_issue_plugin.webbrowser.open", return_value=True)
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_success_prints_message(self, mock_env_fetcher, _mock_open, capsys):
        """Test that success message is printed."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        OpenIssuePlugin().execute(Mock(), Namespace(issue_key="TEST-123"))

        captured = capsys.readouterr()
        assert "🌐 Opening https://jira.example.com/browse/TEST-123 in browser..." in captured.out

    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_failure_no_jira_url(self, mock_env_fetcher):
        """Test handling when JIRA_URL is not set."""
        mock_env_fetcher.get.return_value = None

        with pytest.raises(OpenIssueError) as exc_info:
            OpenIssuePlugin().execute(Mock(), Namespace(issue_key="TEST-123"))

        assert "JIRA_URL not set in environment" in str(exc_info.value)

    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_failure_no_jira_url_prints_message(self, mock_env_fetcher, capsys):
        """Test that error message is printed when JIRA_URL is not set."""
        mock_env_fetcher.get.return_value = None

        with pytest.raises(OpenIssueError):
            OpenIssuePlugin().execute(Mock(), Namespace(issue_key="TEST-123"))

        captured = capsys.readouterr()
        assert "❌ Failed to open issue: JIRA_URL not set in environment" in captured.out

    @patch("jira_creator.plugins.open_issue_plugin.webbrowser.open", return_value=False)
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_failure_no_browser(self, mock_env_fetcher, _mock_open, capsys):
        """Test handling when no browser is available."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        with pytest.raises(OpenIssueError) as exc_info:
            OpenIssuePlugin().execute(Mock(), Namespace(issue_key="TEST-123"))

        assert "No web browser available" in str(exc_info.value)
        assert "❌ Failed to open issue: No web browser available" in capsys.readouterr().out

    @pytest.mark.parametrize("issue_key", ["PROJ-123", "ABC-1", "LONGPROJECT-99999", "X-1234"])
    @patch("jira_creator.plugins.open_issue_plugin.webbrowser.open", return_value=True)
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_with_different_issue_keys(self, mock_env_fetcher, mock_open, issue_key):
        """Test execution with various issue key formats."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        assert OpenIssuePlugin().execute(Mock(), Namespace(issue_key=issue_key)) is True
        mock_open.assert_called_once_with(f"https://jira.example.com/browse/{issue_key}")

    @pytest.mark.parametrize(
        "jira_url",
        [
            "https://jira.company.com",
            "http://jira.local",
            "https://jira.company.com:8080",
            "https://company.atlassian.net",
        ],
    )
    @patch("jira_creator.plugins.open_issue_plugin.webbrowser.open", return_value=True)
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_with_different_jira_urls(self, mock_env_fetcher, mock_open, jira_url):
        """Test execution with various JIRA URL formats."""
        mock_env_fetcher.get.return_value = jira_url

        assert OpenIssuePlugin().execute(Mock(), Namespace(issue_key="TEST-123")) is True
        mock_open.assert_called_once_with(f"{jira_url}/browse/TEST-123")

    @patch("jira_creator.plugins.open_issue_plugin.webbrowser.open", side_effect=OSError("browser launch failed"))
    @patch("jira_creator.plugins.open_issue_plugin.EnvFetcher")
    def test_execute_browser_error(self, mock_env_fetcher, _mock_open):
        """Errors from the browser launcher propagate."""
        mock_env_fetcher.get.return_value = "https://jira.example.com"

        with pytest.raises(OSError):
            OpenIssuePlugin().execute(Mock(), Namespace(issue_key="TEST-123"))
