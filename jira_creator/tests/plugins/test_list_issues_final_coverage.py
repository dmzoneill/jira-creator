#!/usr/bin/env python
"""Tests for final missing branch coverage in list_issues_plugin.py."""

from argparse import Namespace
from unittest.mock import patch

from jira_creator.plugins.list_issues_plugin import ListIssuesPlugin


class TestListIssuesFinalCoverage:
    """Tests for uncovered branches in list_issues_plugin.py."""

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher.get")
    def test_build_jql_query_component_empty_fallback(self, mock_env_get):
        """Test component condition when args.component exists but is empty and env is empty - covers 155->159."""
        # Mock EnvFetcher to return empty string for component
        mock_env_get.side_effect = lambda key, default="": {
            "JIRA_PROJECT_KEY": "TEST",
            "JIRA_COMPONENT_NAME": "",  # Empty component from env
        }.get(key, default)

        plugin = ListIssuesPlugin()

        # Create args where component is empty string (truthy for if check, but falsy after or)
        args = Namespace(
            project="TEST",
            component="",  # Empty string - passes if args.component but results in empty component
            status=None,
            assignee=None,
            reporter=None,
            summary=None,
            blocked=False,
            unblocked=False,
        )

        # Build JQL - should not include component condition due to empty result
        jql = plugin._build_jql_query(args)

        assert jql == "project = TEST"
        assert "component" not in jql

    @patch("jira_creator.plugins.list_issues_plugin.EnvFetcher.get")
    def test_build_jql_query_unblocked_empty_field(self, mock_env_get):
        """Test unblocked condition when JIRA_BLOCKED_FIELD is empty - covers 182->187."""
        # Mock EnvFetcher to return empty string for blocked field
        mock_env_get.side_effect = lambda key, default="": {
            "JIRA_PROJECT_KEY": "TEST",
            "JIRA_BLOCKED_FIELD": "",  # Empty blocked field
        }.get(key, default)

        plugin = ListIssuesPlugin()

        # Create args with unblocked=True but empty blocked field
        args = Namespace(
            project="TEST",
            component=None,
            status=None,
            assignee=None,
            reporter=None,
            summary=None,
            blocked=False,
            unblocked=True,  # This triggers the unblocked logic
        )

        # Build JQL - should not include unblocked condition due to empty blocked field
        jql = plugin._build_jql_query(args)

        assert jql == "project = TEST"
        assert "!=" not in jql
        assert "EMPTY" not in jql
