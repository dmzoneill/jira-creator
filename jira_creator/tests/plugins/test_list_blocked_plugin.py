#!/usr/bin/env python
"""Tests for the list blocked plugin."""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.plugins.list_blocked_plugin import ListBlockedError, ListBlockedPlugin

# Add JIRA_PROJECT_KEY to EnvFetcher vars for testing
if not hasattr(EnvFetcher, "vars") or "JIRA_PROJECT_KEY" not in EnvFetcher.vars:
    if not hasattr(EnvFetcher, "vars"):
        EnvFetcher.vars = {}
    EnvFetcher.vars["JIRA_PROJECT_KEY"] = "TEST"


class TestListBlockedPlugin:
    """Test cases for ListBlockedPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = ListBlockedPlugin()
        assert plugin.command_name == "list-blocked"
        assert "blocked" in plugin.help_text.lower()

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = ListBlockedPlugin()
        mock_parser = Mock(spec=ArgumentParser)

        plugin.register_arguments(mock_parser)

        assert mock_parser.add_argument.call_count == 5

    def test_rest_operation(self):
        """Test the REST operation directly."""
        plugin = ListBlockedPlugin()
        mock_client = Mock()
        mock_response = {"issues": []}
        mock_client.request.return_value = mock_response

        result = plugin.rest_operation(mock_client, jql="project = TEST")

        assert result == mock_response
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "GET"
        assert "/rest/api/2/search" in call_args[0][1]

    @patch("jira_creator.plugins.list_blocked_plugin.EnvFetcher.get")
    def test_build_jql_minimal(self, mock_env):
        """Test building JQL with minimal arguments."""
        plugin = ListBlockedPlugin()
        mock_env.return_value = "TEST"

        args = Namespace(project=None, assignee=None, status=None)
        jql = plugin._build_jql(args)  # pylint: disable=protected-access

        assert 'project = "TEST"' in jql
        assert "status NOT IN" in jql
        assert 'issuelinktype = "Blocks"' in jql.lower() or 'issuelinktype = "blocks"' in jql.lower()

    @patch("jira_creator.plugins.list_blocked_plugin.EnvFetcher.get")
    def test_build_jql_with_filters(self, mock_env):
        """Test building JQL with filters."""
        plugin = ListBlockedPlugin()
        mock_env.return_value = ""

        args = Namespace(project="CUSTOM", assignee="testuser", status="In Progress")
        jql = plugin._build_jql(args)  # pylint: disable=protected-access

        assert 'project = "CUSTOM"' in jql
        assert 'assignee = "testuser"' in jql
        assert 'status = "In Progress"' in jql

    def test_get_blockers(self):
        """Test extracting blocker information."""
        plugin = ListBlockedPlugin()

        fields = {
            "issuelinks": [
                {
                    "type": {"inward": "is blocked by"},
                    "inwardIssue": {
                        "key": "BLOCKER-1",
                        "fields": {"summary": "Blocker issue", "status": {"name": "In Progress"}},
                    },
                },
                {
                    "type": {"outward": "blocks"},
                    "outwardIssue": {
                        "key": "BLOCKED-1",
                        "fields": {"summary": "Blocked issue", "status": {"name": "Open"}},
                    },
                },
            ]
        }

        blockers = plugin._get_blockers(fields)  # pylint: disable=protected-access

        assert len(blockers) == 1
        assert blockers[0]["key"] == "BLOCKER-1"
        assert blockers[0]["summary"] == "Blocker issue"
        assert blockers[0]["status"] == "In Progress"

    def test_get_blockers_empty(self):
        """Test extracting blockers when none exist."""
        plugin = ListBlockedPlugin()

        fields = {"issuelinks": []}
        blockers = plugin._get_blockers(fields)  # pylint: disable=protected-access

        assert blockers == []

    def test_process_issues_without_blockers(self):
        """Test processing issues without fetching blocker details."""
        plugin = ListBlockedPlugin()
        mock_client = Mock()

        issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "summary": "Test issue",
                    "status": {"name": "In Progress"},
                    "priority": {"name": "High"},
                    "assignee": {"displayName": "Test User"},
                },
            }
        ]

        result = plugin._process_issues(mock_client, issues, show_blockers=False)  # pylint: disable=protected-access

        assert len(result) == 1
        assert result[0]["key"] == "TEST-1"
        assert result[0]["summary"] == "Test issue"
        assert "blockers" not in result[0]

    def test_process_issues_with_blockers(self):
        """Test processing issues with blocker details."""
        plugin = ListBlockedPlugin()
        mock_client = Mock()

        issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "summary": "Test issue",
                    "status": {"name": "In Progress"},
                    "priority": {"name": "High"},
                    "assignee": {"displayName": "Test User"},
                    "issuelinks": [
                        {
                            "type": {"inward": "is blocked by"},
                            "inwardIssue": {
                                "key": "BLOCKER-1",
                                "fields": {"summary": "Blocker", "status": {"name": "Open"}},
                            },
                        }
                    ],
                },
            }
        ]

        result = plugin._process_issues(mock_client, issues, show_blockers=True)  # pylint: disable=protected-access

        assert len(result) == 1
        assert "blockers" in result[0]
        assert len(result[0]["blockers"]) == 1

    @patch("builtins.print")
    def test_display_text_without_blockers(self, mock_print):
        """Test text display without blocker details."""
        plugin = ListBlockedPlugin()

        issues = [
            {
                "key": "TEST-1",
                "summary": "Test issue",
                "status": "In Progress",
                "priority": "High",
                "assignee": "Test User",
            }
        ]

        plugin._display_text(issues, show_blockers=False)  # pylint: disable=protected-access

        assert mock_print.called
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("TEST-1" in call for call in print_calls)

    @patch("builtins.print")
    def test_display_text_with_blockers(self, mock_print):
        """Test text display with blocker details."""
        plugin = ListBlockedPlugin()

        issues = [
            {
                "key": "TEST-1",
                "summary": "Test issue",
                "status": "In Progress",
                "priority": "High",
                "assignee": "Test User",
                "blockers": [{"key": "BLOCKER-1", "summary": "Blocker issue", "status": "Open"}],
            }
        ]

        plugin._display_text(issues, show_blockers=True)  # pylint: disable=protected-access

        assert mock_print.called
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("BLOCKER-1" in call for call in print_calls)

    @patch("builtins.print")
    @patch("jira_creator.plugins.list_blocked_plugin.EnvFetcher.get")
    def test_execute_no_issues(self, mock_env, mock_print):
        """Test execution when no blocked issues found."""
        plugin = ListBlockedPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"issues": []}
        mock_env.return_value = "TEST"

        args = Namespace(project=None, assignee=None, status=None, show_blockers=False, output="text")

        result = plugin.execute(mock_client, args)

        assert result is True
        assert any("No blocked issues" in str(call) for call in mock_print.call_args_list)

    @patch("builtins.print")
    @patch("jira_creator.plugins.list_blocked_plugin.EnvFetcher.get")
    def test_execute_with_issues_text(self, mock_env, mock_print):
        """Test execution with issues in text format."""
        plugin = ListBlockedPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "summary": "Test issue",
                        "status": {"name": "In Progress"},
                        "priority": {"name": "High"},
                        "assignee": {"displayName": "Test User"},
                        "issuelinks": [],
                    },
                }
            ]
        }
        mock_env.return_value = "TEST"

        args = Namespace(project=None, assignee=None, status=None, show_blockers=False, output="text")

        result = plugin.execute(mock_client, args)

        assert result is True
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("TEST-1" in call for call in print_calls)

    @patch("builtins.print")
    @patch("jira_creator.plugins.list_blocked_plugin.EnvFetcher.get")
    def test_execute_with_issues_json(self, mock_env, mock_print):
        """Test execution with issues in JSON format."""
        plugin = ListBlockedPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "summary": "Test issue",
                        "status": {"name": "In Progress"},
                        "priority": {"name": "High"},
                        "assignee": {"displayName": "Test User"},
                        "issuelinks": [],
                    },
                }
            ]
        }
        mock_env.return_value = "TEST"

        args = Namespace(project=None, assignee=None, status=None, show_blockers=False, output="json")

        result = plugin.execute(mock_client, args)

        assert result is True
        # Verify JSON was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("TEST-1" in call for call in print_calls)

    @patch("builtins.print")
    @patch("jira_creator.plugins.list_blocked_plugin.EnvFetcher.get")
    def test_execute_list_blocked_error(self, mock_env, mock_print):
        """Test execution when ListBlockedError is raised - covers lines 73-75."""
        plugin = ListBlockedPlugin()
        mock_client = Mock()

        # Make rest_operation raise ListBlockedError
        mock_client.request.side_effect = ListBlockedError("Failed to search blocked issues")
        mock_env.return_value = "TEST"

        args = Namespace(project=None, assignee=None, status=None, show_blockers=False, output="text")

        # Should catch the exception, print error, and re-raise
        with pytest.raises(ListBlockedError) as exc_info:
            plugin.execute(mock_client, args)

        # Verify error was printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Failed to list blocked issues" in call for call in print_calls)
        assert "Failed to search blocked issues" in str(exc_info.value)
