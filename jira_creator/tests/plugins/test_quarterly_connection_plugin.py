#!/usr/bin/env python
"""Tests for the quarterly connection plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import QuarterlyConnectionError
from jira_creator.plugins.quarterly_connection_plugin import QuarterlyConnectionPlugin


class TestQuarterlyConnectionPlugin:
    """Test cases for QuarterlyConnectionPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = QuarterlyConnectionPlugin()
        assert plugin.command_name == "quarterly-connection"
        assert plugin.help_text == "Perform a quarterly connection report"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = QuarterlyConnectionPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        # Currently the plugin doesn't register any arguments
        mock_parser.add_argument.assert_not_called()

    @patch("jira_creator.plugins.quarterly_connection_plugin.get_ai_provider")
    @patch("jira_creator.plugins.quarterly_connection_plugin.EnvFetcher.get")
    def test_rest_operation_successful(self, mock_env_get, mock_get_ai_provider):
        """Test successful REST operation with issues found."""
        # Mock AI provider to prevent actual API calls
        mock_env_get.return_value = None  # No AI provider configured

        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        # Mock user response
        mock_client.request.side_effect = [
            # First call - get current user
            {"name": "test.user", "accountId": "12345"},
            # Second call - search issues
            {
                "issues": [
                    {
                        "key": "TEST-1",
                        "fields": {
                            "summary": "Regular issue",
                            "status": {"name": "Done"},
                            "issuetype": {"name": "Story"},
                        },
                    },
                    {
                        "key": "TEST-2",
                        "fields": {
                            "summary": "CVE-2023-12345 Security Fix",
                            "status": {"name": "In Progress"},
                            "issuetype": {"name": "Bug"},
                        },
                    },
                    {
                        "key": "TEST-3",
                        "fields": {
                            "summary": "Another task",
                            "status": {"name": "Done"},
                            "issuetype": {"name": "Task"},
                        },
                    },
                ]
            },
        ]

        with patch("builtins.print") as mock_print:
            result = plugin.rest_operation(mock_client)

        assert result is True

        # Verify API calls
        assert mock_client.request.call_count == 2

        # Verify JQL query construction
        search_call = mock_client.request.call_args_list[1]
        assert search_call[0][0] == "GET"
        assert search_call[0][1] == "/rest/api/2/search"
        jql = search_call[1]["params"]["jql"]
        assert "assignee = currentUser()" in jql
        assert "reporter = currentUser()" in jql
        assert "comment ~ currentUser()" in jql
        assert "updated >=" in jql

        # Verify print outputs
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert "🏗️ Building employee report" in print_calls
        assert "📊 Found 3 issues for quarterly report" in print_calls
        assert any("📋 Quarterly Summary (2 relevant issues):" in call for call in print_calls)
        assert any("TEST-1: Regular issue" in call for call in print_calls)
        assert any("TEST-3: Another task" in call for call in print_calls)
        # CVE issue should be filtered out
        assert not any("TEST-2" in call for call in print_calls)
        assert any("📈 Issue Types:" in call for call in print_calls)
        assert any("📊 Status Distribution:" in call for call in print_calls)

    def test_rest_operation_no_issues_found(self):
        """Test REST operation when no issues are found."""
        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        mock_client.request.side_effect = [{"name": "test.user"}, {"issues": []}]

        with patch("builtins.print") as mock_print:
            result = plugin.rest_operation(mock_client)

        assert result is True

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        # When issues list is empty, it prints the count and then filters
        assert "📊 Found 0 issues for quarterly report" in print_calls
        assert "✅ No relevant issues found (filtered out CVE issues)" in print_calls

    def test_rest_operation_no_relevant_issues_after_filtering(self):
        """Test REST operation when all issues are CVE issues."""
        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        mock_client.request.side_effect = [
            {"accountId": "12345"},
            {
                "issues": [
                    {
                        "key": "TEST-1",
                        "fields": {
                            "summary": "CVE-2023-12345",
                            "status": {"name": "Done"},
                            "issuetype": {"name": "Bug"},
                        },
                    },
                    {
                        "key": "TEST-2",
                        "fields": {
                            "summary": "Fix for CVE-2023-67890",
                            "status": {"name": "Done"},
                            "issuetype": {"name": "Bug"},
                        },
                    },
                ]
            },
        ]

        with patch("builtins.print") as mock_print:
            result = plugin.rest_operation(mock_client)

        assert result is True

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert "✅ No relevant issues found (filtered out CVE issues)" in print_calls

    def test_rest_operation_user_not_found(self):
        """Test REST operation when user information is not available."""
        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        # Return empty user response
        mock_client.request.return_value = {}

        with patch("builtins.print") as mock_print:
            result = plugin.rest_operation(mock_client)

        assert result is False

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert "❌ Could not get current user information" in print_calls

    @patch("jira_creator.plugins.quarterly_connection_plugin.get_ai_provider")
    @patch("jira_creator.plugins.quarterly_connection_plugin.EnvFetcher.get")
    def test_rest_operation_with_missing_issue_fields(self, mock_env_get, mock_get_ai_provider):
        """Test REST operation with issues missing some fields."""
        # Mock AI provider to prevent actual API calls
        mock_env_get.return_value = None  # No AI provider configured

        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        mock_client.request.side_effect = [
            {"name": "test.user"},
            {
                "issues": [
                    {"key": "TEST-1", "fields": {}},  # Missing all fields
                    {
                        "key": "TEST-2",
                        "fields": {
                            "summary": "Task with partial fields"
                            # Missing status and issuetype
                        },
                    },
                ]
            },
        ]

        with patch("builtins.print") as mock_print:
            result = plugin.rest_operation(mock_client)

        assert result is True

        # Verify issues are processed with default values
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("Unknown" in call for call in print_calls)

    @patch("jira_creator.plugins.quarterly_connection_plugin.PromptLibrary")
    @patch("jira_creator.plugins.quarterly_connection_plugin.EnvFetcher")
    @patch("jira_creator.plugins.quarterly_connection_plugin.get_ai_provider")
    def test_rest_operation_with_ai_enhancement(self, mock_get_ai_provider, mock_env_fetcher, mock_prompt_lib):
        """Test REST operation with AI enhancement."""
        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        # Setup mocks
        mock_env_fetcher.get.return_value = "openai"
        mock_ai_provider = Mock()
        mock_ai_provider.improve_text.return_value = "AI-enhanced quarterly summary: Great progress!"
        mock_get_ai_provider.return_value = mock_ai_provider
        mock_prompt_instance = Mock()
        mock_prompt_instance.get_prompt.return_value = "Enhance this quarterly report"
        mock_prompt_lib.return_value = mock_prompt_instance

        mock_client.request.side_effect = [
            {"name": "test.user"},
            {
                "issues": [
                    {
                        "key": "TEST-1",
                        "fields": {
                            "summary": "Feature implementation",
                            "status": {"name": "Done"},
                            "issuetype": {"name": "Story"},
                        },
                    }
                ]
            },
        ]

        with patch("builtins.print") as mock_print:
            result = plugin.rest_operation(mock_client)

        assert result is True

        # Verify AI enhancement was called
        mock_get_ai_provider.assert_called_once_with("openai")
        mock_ai_provider.improve_text.assert_called_once()

        # Verify AI summary was printed
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("🤖 AI-Enhanced Summary:" in call for call in print_calls)
        assert any("Great progress!" in call for call in print_calls)

    @patch("jira_creator.plugins.quarterly_connection_plugin.EnvFetcher")
    @patch("jira_creator.plugins.quarterly_connection_plugin.get_ai_provider")
    def test_rest_operation_ai_enhancement_failure(self, mock_get_ai_provider, mock_env_fetcher):
        """Test REST operation when AI enhancement fails."""
        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        # Setup mocks
        mock_env_fetcher.get.return_value = "openai"
        mock_get_ai_provider.side_effect = Exception("AI provider not available")

        mock_client.request.side_effect = [
            {"name": "test.user"},
            {
                "issues": [
                    {
                        "key": "TEST-1",
                        "fields": {
                            "summary": "Task",
                            "status": {"name": "Done"},
                            "issuetype": {"name": "Task"},
                        },
                    }
                ]
            },
        ]

        with patch("builtins.print") as mock_print:
            result = plugin.rest_operation(mock_client)

        assert result is True

        # Verify warning about AI unavailability
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("⚠️ AI enhancement unavailable:" in call for call in print_calls)
        assert any("AI provider not available" in call for call in print_calls)

    def test_rest_operation_exception_handling(self):
        """Test REST operation with general exception."""
        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        # Simulate API error
        mock_client.request.side_effect = Exception("API connection failed")

        with pytest.raises(QuarterlyConnectionError) as exc_info:
            plugin.rest_operation(mock_client)

        assert "Error generating quarterly report: API connection failed" in str(exc_info.value)

    def test_execute_successful(self):
        """Test successful execution."""
        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        # Mock successful rest_operation
        with patch.object(plugin, "rest_operation", return_value=True) as mock_rest_op:
            args = Namespace()
            result = plugin.execute(mock_client, args)

        assert result is True
        mock_rest_op.assert_called_once_with(mock_client)

    def test_execute_with_error(self):
        """Test execution with QuarterlyConnectionError."""
        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        # Mock rest_operation to raise error
        with patch.object(plugin, "rest_operation", side_effect=QuarterlyConnectionError("Test error")):
            with patch("builtins.print") as mock_print:
                args = Namespace()

                with pytest.raises(QuarterlyConnectionError):
                    plugin.execute(mock_client, args)

                mock_print.assert_called_with("❌ Failed to generate quarterly connection report: Test error")

    def test_time_calculation(self):
        """Test that time calculation for 90 days is correct."""
        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        # Mock time to a specific value
        mock_time = 1700000000  # Some arbitrary timestamp
        with patch("time.time", return_value=mock_time):
            mock_client.request.side_effect = [{"name": "test.user"}, {"issues": []}]

            plugin.rest_operation(mock_client)

            # Verify the JQL query includes correct time calculation
            search_call = mock_client.request.call_args_list[1]
            jql = search_call[1]["params"]["jql"]

            # Calculate expected time (90 days in milliseconds)
            expected_time = int(mock_time * 1000) - (90 * 24 * 60 * 60 * 1000)
            assert f"updated >= {expected_time}" in jql

    @patch("jira_creator.plugins.quarterly_connection_plugin.get_ai_provider")
    @patch("jira_creator.plugins.quarterly_connection_plugin.EnvFetcher.get")
    def test_issue_type_and_status_counting(self, mock_env_get, mock_get_ai_provider):
        """Test that issue types and statuses are counted correctly."""
        # Mock AI provider to prevent actual API calls
        mock_env_get.return_value = None  # No AI provider configured

        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        mock_client.request.side_effect = [
            {"name": "test.user"},
            {
                "issues": [
                    {
                        "key": "TEST-1",
                        "fields": {
                            "summary": "Story 1",
                            "status": {"name": "Done"},
                            "issuetype": {"name": "Story"},
                        },
                    },
                    {
                        "key": "TEST-2",
                        "fields": {
                            "summary": "Story 2",
                            "status": {"name": "Done"},
                            "issuetype": {"name": "Story"},
                        },
                    },
                    {
                        "key": "TEST-3",
                        "fields": {
                            "summary": "Bug 1",
                            "status": {"name": "In Progress"},
                            "issuetype": {"name": "Bug"},
                        },
                    },
                ]
            },
        ]

        with patch("builtins.print") as mock_print:
            plugin.rest_operation(mock_client)

        print_calls = [call[0][0] for call in mock_print.call_args_list]

        # Verify issue type counts
        assert any("Story: 2" in call for call in print_calls)
        assert any("Bug: 1" in call for call in print_calls)

        # Verify status counts
        assert any("Done: 2" in call for call in print_calls)
        assert any("In Progress: 1" in call for call in print_calls)

    @patch("jira_creator.plugins.quarterly_connection_plugin.get_ai_provider")
    @patch("jira_creator.plugins.quarterly_connection_plugin.EnvFetcher.get")
    def test_summary_truncation(self, mock_env_get, mock_get_ai_provider):  # pylint: disable=unused-argument
        """Test that long summaries are truncated in output."""
        # Mock AI provider to prevent actual API calls
        mock_env_get.return_value = None  # No AI provider configured

        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        long_summary = "A" * 100  # Very long summary

        mock_client.request.side_effect = [
            {"name": "test.user"},
            {
                "issues": [
                    {
                        "key": "TEST-1",
                        "fields": {
                            "summary": long_summary,
                            "status": {"name": "Done"},
                            "issuetype": {"name": "Story"},
                        },
                    }
                ]
            },
        ]

        with patch("builtins.print") as mock_print:
            plugin.rest_operation(mock_client)

        print_calls = [call[0][0] for call in mock_print.call_args_list]

        # Verify summary is truncated to 60 characters with ellipsis
        truncated_summary = long_summary[:60] + "..."
        assert any(f"TEST-1: {truncated_summary}" in call for call in print_calls)

    @patch("jira_creator.plugins.quarterly_connection_plugin.get_ai_provider")
    @patch("jira_creator.plugins.quarterly_connection_plugin.EnvFetcher.get")
    def test_case_insensitive_cve_filtering(
        self, mock_env_get, mock_get_ai_provider
    ):  # pylint: disable=unused-argument
        """Test that CVE filtering is case-insensitive."""
        # Mock AI provider to prevent actual API calls
        mock_env_get.return_value = None  # No AI provider configured

        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        mock_client.request.side_effect = [
            {"name": "test.user"},
            {
                "issues": [
                    {
                        "key": "TEST-1",
                        "fields": {
                            "summary": "Fix cve-2023-12345",  # lowercase
                            "status": {"name": "Done"},
                            "issuetype": {"name": "Bug"},
                        },
                    },
                    {
                        "key": "TEST-2",
                        "fields": {
                            "summary": "Fix Cve-2023-67890",  # mixed case
                            "status": {"name": "Done"},
                            "issuetype": {"name": "Bug"},
                        },
                    },
                    {
                        "key": "TEST-3",
                        "fields": {
                            "summary": "Regular bug fix",
                            "status": {"name": "Done"},
                            "issuetype": {"name": "Bug"},
                        },
                    },
                ]
            },
        ]

        with patch("builtins.print") as mock_print:
            plugin.rest_operation(mock_client)

        print_calls = [call[0][0] for call in mock_print.call_args_list]

        # Only TEST-3 should be included
        assert any("TEST-3" in call for call in print_calls)
        assert not any("TEST-1" in call for call in print_calls)
        assert not any("TEST-2" in call for call in print_calls)
        assert any("📋 Quarterly Summary (1 relevant issues):" in call for call in print_calls)

    def test_max_results_parameter(self):
        """Test that maxResults parameter is set correctly."""
        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        mock_client.request.side_effect = [{"name": "test.user"}, {"issues": []}]

        plugin.rest_operation(mock_client)

        # Verify search call includes maxResults
        search_call = mock_client.request.call_args_list[1]
        assert search_call[1]["params"]["maxResults"] == 1000

    def test_no_issues_key_in_response(self):
        """Test handling when 'issues' key is missing from response."""
        plugin = QuarterlyConnectionPlugin()
        mock_client = Mock()

        mock_client.request.side_effect = [{"name": "test.user"}, {}]  # No 'issues' key

        with patch("builtins.print") as mock_print:
            result = plugin.rest_operation(mock_client)

        assert result is True

        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert "✅ No issues found for quarterly report" in print_calls
