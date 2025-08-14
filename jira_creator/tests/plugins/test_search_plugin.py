#!/usr/bin/env python
"""Tests for the search plugin."""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import SearchError
from jira_creator.plugins.search_plugin import SearchPlugin


class TestSearchPlugin:
    """Test cases for SearchPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = SearchPlugin()
        assert plugin.command_name == "search"
        assert plugin.help_text == "Search for issues using JQL (Jira Query Language)"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = SearchPlugin()
        parser = ArgumentParser()
        plugin.register_arguments(parser)

        # Parse test arguments
        args = parser.parse_args(["project = TEST AND status = Open"])
        assert args.jql == "project = TEST AND status = Open"
        assert args.max_results == 50  # Default value

        # Test with custom max results
        args = parser.parse_args(["project = TEST", "-m", "100"])
        assert args.jql == "project = TEST"
        assert args.max_results == 100

    def test_rest_operation(self):
        """Test the REST operation."""
        plugin = SearchPlugin()
        mock_client = Mock()
        mock_response = {
            "issues": [
                {"key": "TEST-1", "fields": {"summary": "Test Issue 1"}},
                {"key": "TEST-2", "fields": {"summary": "Test Issue 2"}},
            ]
        }
        mock_client.request.return_value = mock_response

        # Call REST operation
        result = plugin.rest_operation(mock_client, jql="project = TEST", max_results=10)

        # Verify the request
        mock_client.request.assert_called_once_with(
            "GET",
            "/rest/api/2/search",
            params={
                "jql": "project = TEST",
                "maxResults": 10,
                "fields": "key,summary,status,assignee,priority,issuetype,created,updated",
            },
        )
        assert result == mock_response["issues"]

    def test_rest_operation_with_default_max_results(self):
        """Test REST operation with default max_results."""
        plugin = SearchPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"issues": []}

        # Call without max_results
        plugin.rest_operation(mock_client, jql="project = TEST")

        # Verify default value was used
        call_args = mock_client.request.call_args
        assert call_args[1]["params"]["maxResults"] == 50

    def test_rest_operation_empty_response(self):
        """Test REST operation with empty response."""
        plugin = SearchPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {}  # No issues key

        result = plugin.rest_operation(mock_client, jql="project = TEST")
        assert result == []

    @patch("jira_creator.plugins.search_plugin.massage_issue_list")
    @patch("jira_creator.plugins.search_plugin.format_and_print_rows")
    def test_execute_with_results(self, mock_format_print, mock_massage):
        """Test execute with search results."""
        plugin = SearchPlugin()
        mock_client = Mock()

        # Mock REST response
        mock_issues = [
            {"key": "TEST-1", "fields": {"summary": "Issue 1"}},
            {"key": "TEST-2", "fields": {"summary": "Issue 2"}},
        ]
        mock_client.request.return_value = {"issues": mock_issues}

        # Mock massage function
        mock_massaged = [
            {"Key": "TEST-1", "Summary": "Issue 1"},
            {"Key": "TEST-2", "Summary": "Issue 2"},
        ]
        mock_massage.return_value = mock_massaged

        # Create args
        args = Namespace(jql="project = TEST", max_results=50)

        # Execute
        result = plugin.execute(mock_client, args)

        # Verify
        assert result is True
        mock_client.request.assert_called_once()
        mock_massage.assert_called_once_with(mock_issues, mock_client)
        mock_format_print.assert_called_once_with(mock_massaged, [], mock_client)

        # Verify print output was called
        # Note: We can't easily capture print statements, but the test ensures
        # the code path is executed

    @patch("jira_creator.plugins.search_plugin.massage_issue_list")
    @patch("jira_creator.plugins.search_plugin.format_and_print_rows")
    def test_execute_with_no_results(self, mock_format_print, mock_massage):
        """Test execute with no search results."""
        plugin = SearchPlugin()
        mock_client = Mock()

        # Mock empty REST response
        mock_client.request.return_value = {"issues": []}

        # Create args
        args = Namespace(jql="project = NONEXISTENT", max_results=50)

        # Execute
        result = plugin.execute(mock_client, args)

        # Verify
        assert result is True
        mock_client.request.assert_called_once()
        # massage_issue_list and format_and_print_rows should not be called
        mock_massage.assert_not_called()
        mock_format_print.assert_not_called()

    def test_execute_with_search_error(self):
        """Test execute when search fails - generic exception is not caught."""
        plugin = SearchPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = Exception("API Error")

        args = Namespace(jql="invalid JQL", max_results=50)

        # The plugin doesn't catch generic exceptions, only SearchError
        with pytest.raises(Exception) as exc_info:
            plugin.execute(mock_client, args)

        assert str(exc_info.value) == "API Error"

    @patch("jira_creator.plugins.search_plugin.massage_issue_list")
    def test_execute_with_massage_error(self, mock_massage):
        """Test execute when massage_issue_list fails - generic exception is not caught."""
        plugin = SearchPlugin()
        mock_client = Mock()

        # Mock REST response
        mock_client.request.return_value = {"issues": [{"key": "TEST-1"}]}
        mock_massage.side_effect = Exception("Massage failed")

        args = Namespace(jql="project = TEST", max_results=50)

        # The plugin doesn't catch generic exceptions from massage_issue_list
        with pytest.raises(Exception) as exc_info:
            plugin.execute(mock_client, args)

        assert str(exc_info.value) == "Massage failed"

    def test_execute_with_different_max_results(self):
        """Test execute with various max_results values."""
        plugin = SearchPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"issues": []}

        # Test with different max_results
        for max_results in [1, 10, 100, 1000]:
            args = Namespace(jql="project = TEST", max_results=max_results)
            result = plugin.execute(mock_client, args)
            assert result is True

            # Verify the correct max_results was passed
            call_args = mock_client.request.call_args
            assert call_args[1]["params"]["maxResults"] == max_results

    @patch("builtins.print")
    @patch("jira_creator.plugins.search_plugin.format_and_print_rows")
    @patch("jira_creator.plugins.search_plugin.massage_issue_list")
    def test_execute_print_statements(self, mock_massage, mock_format_print, mock_print):
        """Test that correct print statements are made."""
        plugin = SearchPlugin()
        mock_client = Mock()

        # Mock massage_issue_list to return proper format
        mock_massage.return_value = [{"Key": "TEST-1"}, {"Key": "TEST-2"}]

        # Test with results
        mock_client.request.return_value = {"issues": [{"key": "TEST-1"}, {"key": "TEST-2"}]}
        args = Namespace(jql="project = TEST", max_results=50)
        plugin.execute(mock_client, args)

        # Check for the found message
        mock_print.assert_any_call("\n📊 Found 2 issue(s)")

        # Reset and test with no results
        mock_print.reset_mock()
        mock_client.request.return_value = {"issues": []}
        plugin.execute(mock_client, args)

        # Check for the no results message
        mock_print.assert_any_call("📭 No issues found matching your query")

    def test_complex_jql_queries(self):
        """Test with various complex JQL queries."""
        plugin = SearchPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"issues": []}

        # Test various JQL queries
        test_queries = [
            "project = TEST AND status = 'In Progress'",
            "assignee = currentUser() AND created >= -7d",
            "labels in (bug, critical) ORDER BY priority DESC",
            'text ~ "search term" AND resolution is EMPTY',
        ]

        for jql in test_queries:
            args = Namespace(jql=jql, max_results=50)
            result = plugin.execute(mock_client, args)
            assert result is True

            # Verify the JQL was passed correctly
            call_args = mock_client.request.call_args
            assert call_args[1]["params"]["jql"] == jql

    def test_execute_with_search_error_exception(self, capsys):
        """Test handling of SearchError during execution."""
        plugin = SearchPlugin()
        mock_client = Mock()

        # Make the request raise SearchError
        mock_client.request.side_effect = SearchError("Invalid JQL syntax")

        args = Namespace(jql="invalid query syntax", max_results=50)

        # Verify SearchError is raised
        with pytest.raises(SearchError) as exc_info:
            plugin.execute(mock_client, args)

        assert "Invalid JQL syntax" in str(exc_info.value)

        # Verify error message is printed
        captured = capsys.readouterr()
        assert "❌ Search failed: Invalid JQL syntax" in captured.out
