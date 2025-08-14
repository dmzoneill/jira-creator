#!/usr/bin/env python
"""Tests for the search users plugin."""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import SearchUsersError
from jira_creator.plugins.search_users_plugin import SearchUsersPlugin


class TestSearchUsersPlugin:
    """Test cases for SearchUsersPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = SearchUsersPlugin()
        assert plugin.command_name == "search-users"
        assert plugin.help_text == "Search for Jira users by name or email"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = SearchUsersPlugin()
        parser = ArgumentParser()
        plugin.register_arguments(parser)

        # Parse test arguments
        args = parser.parse_args(["john.doe"])
        assert args.query == "john.doe"
        assert args.max_results == 50  # Default value

        # Test with custom max results
        args = parser.parse_args(["jane@example.com", "-m", "25"])
        assert args.query == "jane@example.com"
        assert args.max_results == 25

        # Test with email query
        args = parser.parse_args(["user@domain.com", "--max-results", "100"])
        assert args.query == "user@domain.com"
        assert args.max_results == 100

    def test_rest_operation(self):
        """Test the REST operation."""
        plugin = SearchUsersPlugin()
        mock_client = Mock()
        mock_response = [
            {
                "name": "jdoe",
                "displayName": "John Doe",
                "emailAddress": "john@example.com",
                "active": True,
            },
            {
                "name": "jsmith",
                "displayName": "Jane Smith",
                "emailAddress": "jane@example.com",
                "active": False,
            },
        ]
        mock_client.request.return_value = mock_response

        # Call REST operation
        result = plugin.rest_operation(mock_client, query="john", max_results=10)

        # Verify the request
        mock_client.request.assert_called_once_with(
            "GET",
            "/rest/api/2/user/search",
            params={"query": "john", "maxResults": 10},
        )
        assert result == mock_response

    def test_rest_operation_with_default_max_results(self):
        """Test REST operation with default max_results."""
        plugin = SearchUsersPlugin()
        mock_client = Mock()
        mock_client.request.return_value = []

        # Call without max_results
        plugin.rest_operation(mock_client, query="test@example.com")

        # Verify default value was used
        call_args = mock_client.request.call_args
        assert call_args[1]["params"]["maxResults"] == 50

    def test_display_user(self):
        """Test the _display_user method."""
        plugin = SearchUsersPlugin()

        # Test with all fields present
        user = {
            "name": "jdoe",
            "displayName": "John Doe",
            "emailAddress": "john@example.com",
            "active": True,
        }

        # Capture print output
        with patch("builtins.print") as mock_print:
            plugin._display_user(user)

            # Verify all fields were printed
            calls = [call.args[0] for call in mock_print.call_args_list]
            assert "\n  Username: jdoe" in calls
            assert "  Name: John Doe" in calls
            assert "  Email: john@example.com" in calls
            assert "  Status: Active" in calls
            assert "-" * 60 in calls

    def test_display_user_with_missing_fields(self):
        """Test _display_user with missing fields."""
        plugin = SearchUsersPlugin()

        # Test with missing fields
        user = {"active": False}  # Minimal user data

        with patch("builtins.print") as mock_print:
            plugin._display_user(user)

            # Verify N/A values were used
            calls = [call.args[0] for call in mock_print.call_args_list]
            assert "\n  Username: N/A" in calls
            assert "  Name: N/A" in calls
            assert "  Email: N/A" in calls
            assert "  Status: Inactive" in calls

    def test_execute_with_results(self):
        """Test execute with search results."""
        plugin = SearchUsersPlugin()
        mock_client = Mock()

        # Mock REST response
        mock_users = [
            {
                "name": "jdoe",
                "displayName": "John Doe",
                "emailAddress": "john@example.com",
                "active": True,
            },
            {
                "name": "jsmith",
                "displayName": "Jane Smith",
                "emailAddress": "jane@example.com",
                "active": False,
            },
        ]
        mock_client.request.return_value = mock_users

        # Create args
        args = Namespace(query="john", max_results=50)

        # Execute with print mocked
        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

            # Verify
            assert result is True
            mock_client.request.assert_called_once()

            # Check header was printed
            calls = [call.args[0] for call in mock_print.call_args_list]
            assert "\n👥 Found 2 user(s):" in calls
            assert "=" * 60 in calls

            # Verify users were displayed
            assert "\n  Username: jdoe" in calls
            assert "\n  Username: jsmith" in calls

    def test_execute_with_no_results(self):
        """Test execute with no search results."""
        plugin = SearchUsersPlugin()
        mock_client = Mock()

        # Mock empty REST response
        mock_client.request.return_value = []

        # Create args
        args = Namespace(query="nonexistent", max_results=50)

        # Execute with print mocked
        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

            # Verify
            assert result is True
            mock_client.request.assert_called_once()

            # Check no results message
            mock_print.assert_any_call("📭 No users found matching your query")

    def test_execute_with_search_error(self):
        """Test execute when search fails - generic exception is not caught."""
        plugin = SearchUsersPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = Exception("API Error")

        args = Namespace(query="test", max_results=50)

        # The plugin doesn't catch generic exceptions, only SearchUsersError
        with pytest.raises(Exception) as exc_info:
            plugin.execute(mock_client, args)

        assert str(exc_info.value) == "API Error"

    def test_execute_with_display_error(self):
        """Test execute when display fails - generic exception is not caught."""
        plugin = SearchUsersPlugin()
        mock_client = Mock()
        mock_client.request.return_value = [{"name": "test"}]

        # Mock _display_user to raise an error
        with patch.object(plugin, "_display_user", side_effect=Exception("Display error")):
            args = Namespace(query="test", max_results=50)

            # The plugin doesn't catch generic exceptions from _display_user
            with pytest.raises(Exception) as exc_info:
                plugin.execute(mock_client, args)

            assert str(exc_info.value) == "Display error"

    def test_execute_with_different_max_results(self):
        """Test execute with various max_results values."""
        plugin = SearchUsersPlugin()
        mock_client = Mock()
        mock_client.request.return_value = []

        # Test with different max_results
        for max_results in [1, 10, 100, 500]:
            args = Namespace(query="test", max_results=max_results)
            result = plugin.execute(mock_client, args)
            assert result is True

            # Verify the correct max_results was passed
            call_args = mock_client.request.call_args
            assert call_args[1]["params"]["maxResults"] == max_results

    def test_different_query_types(self):
        """Test with various query types."""
        plugin = SearchUsersPlugin()
        mock_client = Mock()
        mock_client.request.return_value = []

        # Test various queries
        test_queries = [
            "john",  # Name search
            "john.doe",  # Username search
            "john@example.com",  # Email search
            "John Doe",  # Full name search
            "j",  # Single character
            "test@domain.co.uk",  # International domain
        ]

        for query in test_queries:
            args = Namespace(query=query, max_results=50)
            result = plugin.execute(mock_client, args)
            assert result is True

            # Verify the query was passed correctly
            call_args = mock_client.request.call_args
            assert call_args[1]["params"]["query"] == query

    @patch("builtins.print")
    def test_execute_print_formatting(self, mock_print):
        """Test print formatting for multiple users."""
        plugin = SearchUsersPlugin()
        mock_client = Mock()

        # Create multiple users with varying data
        mock_users = [
            {
                "name": "admin",
                "displayName": "Administrator",
                "emailAddress": "admin@company.com",
                "active": True,
            },
            {
                "name": "inactive.user",
                "displayName": "Inactive User",
                "active": False,  # No email
            },
            {
                "name": "test.user",
                # No display name
                "emailAddress": "test@company.com",
                "active": True,
            },
        ]
        mock_client.request.return_value = mock_users

        args = Namespace(query="company", max_results=50)
        plugin.execute(mock_client, args)

        # Verify formatting
        calls = [call.args[0] for call in mock_print.call_args_list]

        # Check header
        assert "\n👥 Found 3 user(s):" in calls
        assert "=" * 60 in calls

        # Check each user was displayed
        assert "\n  Username: admin" in calls
        assert "  Name: Administrator" in calls
        assert "  Email: admin@company.com" in calls
        assert "  Status: Active" in calls

        assert "\n  Username: inactive.user" in calls
        assert "  Name: Inactive User" in calls
        assert "  Email: N/A" in calls  # Missing email
        assert "  Status: Inactive" in calls

        assert "\n  Username: test.user" in calls
        assert "  Name: N/A" in calls  # Missing display name
        assert "  Email: test@company.com" in calls
        assert "  Status: Active" in calls

        # Check separators
        separator_count = calls.count("-" * 60)
        assert separator_count == 3  # One for each user

    def test_error_message_formatting(self):
        """Test error message formatting with SearchUsersError."""
        plugin = SearchUsersPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = SearchUsersError("Connection timeout")

        args = Namespace(query="test", max_results=50)

        with patch("builtins.print") as mock_print:
            with pytest.raises(SearchUsersError):
                plugin.execute(mock_client, args)

            # Verify error message was printed
            mock_print.assert_any_call("❌ Failed to search users: Connection timeout")
