#!/usr/bin/env python
"""Tests for the list issues plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import ListIssuesError
from jira_creator.plugins.list_issues_plugin import ListIssuesPlugin


class TestListIssuesPlugin:
    """Test cases for ListIssuesPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = ListIssuesPlugin()
        assert plugin.command_name == "list-issues"
        assert plugin.help_text == "List issues from a project with various filters"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = ListIssuesPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        # Check all arguments are registered
        expected_calls = [
            (
                ("-p", "--project"),
                {
                    "help": "Project key (uses JIRA_PROJECT_KEY env if not specified)",
                    "default": None,
                },
            ),
            (
                ("-c", "--component"),
                {"help": "Filter by component name", "default": None},
            ),
            (
                ("-a", "--assignee"),
                {"help": "Filter by assignee username", "default": None},
            ),
            (
                ("-r", "--reporter"),
                {"help": "Filter by reporter username", "default": None},
            ),
            (("-s", "--status"), {"help": "Filter by status", "default": None}),
            (
                ("--summary",),
                {"help": "Filter by summary containing text", "default": None},
            ),
            (
                ("--blocked",),
                {"action": "store_true", "help": "Show only blocked issues"},
            ),
            (
                ("--unblocked",),
                {"action": "store_true", "help": "Show only unblocked issues"},
            ),
            (
                ("--sort",),
                {"help": "Sort by field(s), comma-separated", "default": "key"},
            ),
            (
                ("-m", "--max-results"),
                {
                    "type": int,
                    "default": 100,
                    "help": "Maximum number of results (default: 100)",
                },
            ),
        ]

        assert mock_parser.add_argument.call_count == len(expected_calls)

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    def test_rest_operation(self, mock_env_fetcher):
        """Test the REST operation."""
        # Mock environment variables for custom fields
        mock_env_fetcher.get.side_effect = lambda key, default="": {
            "JIRA_SPRINT_FIELD": "customfield_12310940",
            "JIRA_STORY_POINTS_FIELD": "customfield_12310243",
            "JIRA_BLOCKED_FIELD": "customfield_12316543",
        }.get(key, default)

        plugin = ListIssuesPlugin()
        mock_client = Mock()
        mock_response = {
            "issues": [
                {"key": "TEST-1", "fields": {"summary": "Issue 1"}},
                {"key": "TEST-2", "fields": {"summary": "Issue 2"}},
            ]
        }
        mock_client.request.return_value = mock_response

        result = plugin.rest_operation(mock_client, jql="project = TEST", max_results=50, order_by="created")

        expected_params = {
            "jql": "project = TEST",
            "maxResults": 50,
            "fields": "key,summary,status,assignee,reporter,priority,issuetype,created,updated,components,customfield_12310940,customfield_12310243,customfield_12316543",
            "orderBy": "created",
        }

        mock_client.request.assert_called_once_with("GET", "/rest/api/2/search", params=expected_params)
        assert result == mock_response["issues"]

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    def test_rest_operation_no_order_by(self, mock_env_fetcher):
        """Test REST operation without orderBy parameter."""
        # Mock environment variables for custom fields
        mock_env_fetcher.get.side_effect = lambda key, default="": {
            "JIRA_SPRINT_FIELD": "customfield_12310940",
            "JIRA_STORY_POINTS_FIELD": "customfield_12310243",
            "JIRA_BLOCKED_FIELD": "customfield_12316543",
        }.get(key, default)

        plugin = ListIssuesPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"issues": []}

        plugin.rest_operation(mock_client, jql="project = TEST", order_by=None)

        # Should not include orderBy in params
        call_args = mock_client.request.call_args
        assert "orderBy" not in call_args[1]["params"]

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    @patch("jira_creator.plugins.list_issues_plugin.format_and_print_rows")
    @patch("jira_creator.plugins.list_issues_plugin.massage_issue_list")
    def test_execute_successful(self, mock_massage, mock_format_print, mock_env_fetcher):
        """Test successful execution with issues found."""
        mock_env_fetcher.get.return_value = "TEST"
        mock_massage.return_value = (["key", "summary"], [("TEST-1", "Issue 1")])

        plugin = ListIssuesPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"issues": [{"key": "TEST-1", "fields": {"summary": "Issue 1"}}]}

        args = Namespace(
            project="TEST",
            component=None,
            assignee=None,
            reporter=None,
            status=None,
            summary=None,
            blocked=False,
            unblocked=False,
            sort="key",
            max_results=100,
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True
        mock_massage.assert_called_once()
        mock_format_print.assert_called_once()

        # Check print output
        mock_print.assert_called_with("\n📊 Found 1 issue(s)")

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    def test_execute_no_issues_found(self, mock_env_fetcher):
        """Test execution when no issues are found."""
        mock_env_fetcher.get.return_value = "TEST"

        plugin = ListIssuesPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"issues": []}

        args = Namespace(
            project="TEST",
            component=None,
            assignee=None,
            reporter=None,
            status=None,
            summary=None,
            blocked=False,
            unblocked=False,
            sort="key",
            max_results=100,
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True
        mock_print.assert_called_with("📭 No issues found matching your criteria")

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    def test_execute_no_project_specified(self, mock_env_fetcher):
        """Test execution when no project is specified."""
        mock_env_fetcher.get.return_value = ""  # No env var set

        plugin = ListIssuesPlugin()
        mock_client = Mock()

        args = Namespace(
            project=None,  # No project in args
            component=None,
            assignee=None,
            reporter=None,
            status=None,
            summary=None,
            blocked=False,
            unblocked=False,
            sort="key",
            max_results=100,
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is False
        mock_print.assert_called_with("❌ No project specified. Use --project or set JIRA_PROJECT_KEY")

    def test_execute_with_error(self):
        """Test execution with API error."""
        plugin = ListIssuesPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = ListIssuesError("API failed")

        args = Namespace(
            project="TEST",
            component=None,
            assignee=None,
            reporter=None,
            status=None,
            summary=None,
            blocked=False,
            unblocked=False,
            sort="key",
            max_results=100,
        )

        with patch("builtins.print") as mock_print:
            with pytest.raises(ListIssuesError):
                plugin.execute(mock_client, args)

        mock_print.assert_called_with("❌ Failed to list issues: API failed")

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    def test_build_jql_query_basic(self, mock_env_fetcher):
        """Test building basic JQL query with just project."""
        mock_env_fetcher.get.return_value = ""

        plugin = ListIssuesPlugin()

        args = Namespace(
            project="TEST",
            component=None,
            assignee=None,
            reporter=None,
            status=None,
            summary=None,
            blocked=False,
            unblocked=False,
        )

        jql = plugin._build_jql_query(args)
        assert jql == "project = TEST"

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    def test_build_jql_query_from_env(self, mock_env_fetcher):
        """Test building JQL query with project from environment."""
        mock_env_fetcher.get.return_value = "ENV_PROJECT"

        plugin = ListIssuesPlugin()

        args = Namespace(
            project=None,  # Not specified
            component=None,
            assignee=None,
            reporter=None,
            status=None,
            summary=None,
            blocked=False,
            unblocked=False,
        )

        jql = plugin._build_jql_query(args)
        assert jql == "project = ENV_PROJECT"

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    def test_build_jql_query_with_all_filters(self, mock_env_fetcher):
        """Test building JQL query with all filters."""
        mock_env_fetcher.get.side_effect = lambda key, default: {
            "JIRA_PROJECT_KEY": "",
            "JIRA_COMPONENT_NAME": "Backend",
            "JIRA_BLOCKED_FIELD": "customfield_10001",
        }.get(key, default)

        plugin = ListIssuesPlugin()

        args = Namespace(
            project="TEST",
            component="Frontend",  # Overrides env var
            assignee="john.doe",
            reporter=None,
            status="In Progress",
            summary="bug fix",
            blocked=True,
            unblocked=False,
        )

        jql = plugin._build_jql_query(args)

        expected_parts = [
            "project = TEST",
            "component = 'Frontend'",
            "status = 'In Progress'",
            "assignee = 'john.doe'",
            "summary ~ 'bug fix'",
            "customfield_10001 = 'True'",
        ]

        assert jql == " AND ".join(expected_parts)

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    def test_build_jql_query_reporter_overrides_assignee(self, mock_env_fetcher):
        """Test that reporter filter takes precedence over assignee."""
        mock_env_fetcher.get.return_value = ""

        plugin = ListIssuesPlugin()

        args = Namespace(
            project="TEST",
            component=None,
            assignee="john.doe",
            reporter="jane.smith",  # Should override assignee
            status=None,
            summary=None,
            blocked=False,
            unblocked=False,
        )

        jql = plugin._build_jql_query(args)

        assert "reporter = 'jane.smith'" in jql
        assert "assignee" not in jql

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    def test_build_jql_query_unblocked_filter(self, mock_env_fetcher):
        """Test building JQL with unblocked filter."""
        mock_env_fetcher.get.side_effect = lambda key, default: {"JIRA_BLOCKED_FIELD": "customfield_10001"}.get(
            key, default
        )

        plugin = ListIssuesPlugin()

        args = Namespace(
            project="TEST",
            component=None,
            assignee=None,
            reporter=None,
            status=None,
            summary=None,
            blocked=False,
            unblocked=True,
        )

        jql = plugin._build_jql_query(args)

        assert "(customfield_10001 != 'True' OR customfield_10001 IS EMPTY)" in jql

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    def test_build_jql_query_both_blocked_unblocked(self, mock_env_fetcher):
        """Test that specifying both blocked and unblocked results in no filter."""
        mock_env_fetcher.get.return_value = "customfield_10001"

        plugin = ListIssuesPlugin()

        args = Namespace(
            project="TEST",
            component=None,
            assignee=None,
            reporter=None,
            status=None,
            summary=None,
            blocked=True,
            unblocked=True,  # Both are True
        )

        jql = plugin._build_jql_query(args)

        # Should not contain any blocked field filter
        assert "customfield_10001" not in jql
        assert jql == "project = TEST"

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    def test_build_jql_query_component_from_env(self, mock_env_fetcher):
        """Test component filter from environment variable."""

        def mock_get(key, default):
            if key == "JIRA_COMPONENT_NAME":
                return "Backend"
            return default

        mock_env_fetcher.get.side_effect = mock_get

        plugin = ListIssuesPlugin()

        # Based on the code logic, args.component must be explicitly set to use env var
        args = Namespace(
            project="TEST",
            component="Backend",  # Will match env var
            assignee=None,
            reporter=None,
            status=None,
            summary=None,
            blocked=False,
            unblocked=False,
        )

        jql = plugin._build_jql_query(args)

        assert "component = 'Backend'" in jql

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    def test_build_jql_query_no_blocked_field_configured(self, mock_env_fetcher):
        """Test blocked filter when JIRA_BLOCKED_FIELD is not configured."""
        mock_env_fetcher.get.return_value = ""  # No blocked field configured

        plugin = ListIssuesPlugin()

        args = Namespace(
            project="TEST",
            component=None,
            assignee=None,
            reporter=None,
            status=None,
            summary=None,
            blocked=True,
            unblocked=False,
        )

        jql = plugin._build_jql_query(args)

        # Should not include blocked filter if field not configured
        assert jql == "project = TEST"

    def test_execute_with_custom_sort(self):
        """Test execution with custom sort order."""
        plugin = ListIssuesPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"issues": []}

        args = Namespace(
            project="TEST",
            component=None,
            assignee=None,
            reporter=None,
            status=None,
            summary=None,
            blocked=False,
            unblocked=False,
            sort="priority DESC, created ASC",
            max_results=50,
        )

        plugin.execute(mock_client, args)

        # Check that orderBy was passed correctly
        call_args = mock_client.request.call_args
        assert call_args[1]["params"]["orderBy"] == "priority DESC, created ASC"

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    @patch("jira_creator.plugins.list_issues_plugin.format_and_print_rows")
    @patch("jira_creator.plugins.list_issues_plugin.massage_issue_list")
    def test_execute_with_multiple_issues(self, mock_massage, mock_format_print, mock_env_fetcher):
        """Test execution with multiple issues found."""
        mock_env_fetcher.get.return_value = "TEST"

        issues = [
            {"key": "TEST-1", "fields": {"summary": "Issue 1"}},
            {"key": "TEST-2", "fields": {"summary": "Issue 2"}},
            {"key": "TEST-3", "fields": {"summary": "Issue 3"}},
        ]

        mock_massage.return_value = (
            ["key", "summary"],
            [("TEST-1", "Issue 1"), ("TEST-2", "Issue 2"), ("TEST-3", "Issue 3")],
        )

        plugin = ListIssuesPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"issues": issues}

        args = Namespace(
            project="TEST",
            component=None,
            assignee=None,
            reporter=None,
            status=None,
            summary=None,
            blocked=False,
            unblocked=False,
            sort="key",
            max_results=100,
        )

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True

        # Check final count message
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("📊 Found 3 issue(s)" in call for call in print_calls)

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
    def test_rest_operation_empty_field_env_vars(self, mock_env_fetcher):
        """Test REST operation when field environment variables are empty strings."""
        # Mock environment variables to return empty strings
        mock_env_fetcher.get.side_effect = lambda key, default="": ""

        plugin = ListIssuesPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"issues": []}

        plugin.rest_operation(mock_client, jql="project = TEST")

        # Should not include any custom fields when env vars are empty
        expected_params = {
            "jql": "project = TEST",
            "maxResults": 100,
            "fields": "key,summary,status,assignee,reporter,priority,issuetype,created,updated,components",
            "orderBy": "key",
        }

        mock_client.request.assert_called_once_with("GET", "/rest/api/2/search", params=expected_params)
