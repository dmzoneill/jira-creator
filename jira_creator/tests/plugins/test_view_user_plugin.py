#!/usr/bin/env python
"""Tests for the view user plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import GetUserError
from jira_creator.plugins.view_user_plugin import ViewUserPlugin


class TestViewUserPlugin:
    """Test cases for ViewUserPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = ViewUserPlugin()
        assert plugin.command_name == "view-user"
        assert plugin.help_text == "View detailed information about a Jira user"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = ViewUserPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        mock_parser.add_argument.assert_called_once_with("account_id", help="The user's account ID or username")

    def test_rest_operation_with_account_id(self):
        """Test REST operation with account ID success."""
        plugin = ViewUserPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {
            "accountId": "12345",
            "displayName": "John Doe",
        }

        result = plugin.rest_operation(mock_client, account_id="12345")

        mock_client.request.assert_called_once_with("GET", "/rest/api/2/user?accountId=12345")
        assert result == {"accountId": "12345", "displayName": "John Doe"}

    def test_rest_operation_fallback_to_username(self):
        """Test REST operation falls back to username when account ID fails."""
        plugin = ViewUserPlugin()
        mock_client = Mock()

        # First call fails, second succeeds
        mock_client.request.side_effect = [
            Exception("Account ID not found"),
            {"accountId": "12345", "displayName": "John Doe"},
        ]

        result = plugin.rest_operation(mock_client, account_id="johndoe")

        # Should have been called twice
        assert mock_client.request.call_count == 2
        mock_client.request.assert_any_call("GET", "/rest/api/2/user?accountId=johndoe")
        mock_client.request.assert_any_call("GET", "/rest/api/2/user?username=johndoe")
        assert result == {"accountId": "12345", "displayName": "John Doe"}

    def test_execute_successful(self):
        """Test successful execution."""
        plugin = ViewUserPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {
            "accountId": "12345",
            "displayName": "John Doe",
            "emailAddress": "john.doe@example.com",
            "active": True,
            "timeZone": "America/New_York",
            "locale": "en_US",
            "self": "https://jira.example.com/rest/api/2/user?accountId=12345",
            "avatarUrls": {"48x48": "https://example.com/avatar.png"},
            "groups": {"size": 5, "items": []},
            "applicationRoles": {"size": 2, "items": []},
            "expand": "groups,applicationRoles",
        }

        args = Namespace(account_id="12345")

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_called_once()

        # Verify print output
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("👤 User Details: John Doe" in call for call in print_calls)
        assert any("john.doe@example.com" in call for call in print_calls)

    def test_execute_with_error(self):
        """Test execution with API error."""
        plugin = ViewUserPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = GetUserError("User not found")

        args = Namespace(account_id="unknown-user")

        with patch("builtins.print") as mock_print:
            with pytest.raises(GetUserError):
                plugin.execute(mock_client, args)

        # Verify error message was printed
        mock_print.assert_called_with("❌ Failed to get user details: User not found")

    def test_display_user_details_filters_fields(self):
        """Test that display_user_details filters out unwanted fields."""
        plugin = ViewUserPlugin()

        user_data = {
            "accountId": "12345",
            "displayName": "John Doe",
            "emailAddress": "john@example.com",
            "active": True,
            "self": "https://jira.example.com/user",  # Should be filtered
            "avatarUrls": {"48x48": "url"},  # Should be filtered
            "ownerId": "owner123",  # Should be filtered
            "applicationRoles": {"items": []},  # Should be filtered
            "groups": {"items": []},  # Should be filtered
            "expand": "groups",  # Should be filtered
        }

        with patch("builtins.print") as mock_print:
            plugin._display_user_details(user_data)

        print_calls = [call[0][0] for call in mock_print.call_args_list]

        # Verify filtered fields are not displayed
        assert not any("self" in call.lower() for call in print_calls)
        assert not any("avatarurls" in call.lower() for call in print_calls)
        assert not any("ownerid" in call.lower() for call in print_calls)
        assert not any("applicationroles" in call.lower() for call in print_calls)
        assert not any("groups" in call.lower() for call in print_calls)
        assert not any("expand" in call.lower() for call in print_calls)

        # Verify kept fields are displayed
        assert any("john@example.com" in call for call in print_calls)
        assert any("12345" in call for call in print_calls)

    def test_display_user_details_handles_none_values(self):
        """Test that display handles None values correctly."""
        plugin = ViewUserPlugin()

        user_data = {
            "accountId": "12345",
            "displayName": "John Doe",
            "emailAddress": None,  # None value should be filtered out
            "locale": None,
        }

        with patch("builtins.print") as mock_print:
            plugin._display_user_details(user_data)

        print_calls = [call[0][0] for call in mock_print.call_args_list]

        # None values should not appear
        assert not any("emailAddress" in call.lower() for call in print_calls)
        assert not any("locale" in call.lower() for call in print_calls)

    def test_display_user_details_formats_boolean_values(self):
        """Test that boolean values are formatted as Yes/No."""
        plugin = ViewUserPlugin()

        user_data = {
            "displayName": "John Doe",
            "active": True,
            "verified": False,
        }

        with patch("builtins.print") as mock_print:
            plugin._display_user_details(user_data)

        print_calls = [call[0][0] for call in mock_print.call_args_list]

        # Check boolean formatting
        assert any("Yes" in call for call in print_calls)  # For active: True
        assert any("No" in call for call in print_calls)  # For verified: False

    def test_display_user_details_formats_list_values(self):
        """Test that list values are formatted correctly."""
        plugin = ViewUserPlugin()

        user_data = {
            "displayName": "John Doe",
            "roles": ["admin", "developer", "reviewer"],
            "permissions": [],  # Empty list
        }

        with patch("builtins.print") as mock_print:
            plugin._display_user_details(user_data)

        print_calls = [call[0][0] for call in mock_print.call_args_list]

        # Check list formatting
        assert any("admin, developer, reviewer" in call for call in print_calls)
        assert any("None" in call for call in print_calls)  # Empty list shows as None

    def test_display_user_details_formats_field_names(self):
        """Test that field names are formatted nicely."""
        plugin = ViewUserPlugin()

        user_data = {
            "displayName": "John Doe",
            "email_address": "john@example.com",
            "created-date": "2024-01-01",
            "accountId": "12345",
        }

        with patch("builtins.print") as mock_print:
            plugin._display_user_details(user_data)

        print_calls = [call[0][0] for call in mock_print.call_args_list]

        # Check field name formatting
        assert any("Email Address" in call for call in print_calls)  # Underscores to spaces
        assert any("Created Date" in call for call in print_calls)  # Hyphens to spaces
        assert any("Accountid" in call for call in print_calls)  # Title case

    def test_display_user_details_with_minimal_data(self):
        """Test display with minimal user data."""
        plugin = ViewUserPlugin()

        user_data = {
            "displayName": None,  # Will show as "Unknown" in header
            "accountId": "12345",
        }

        with patch("builtins.print") as mock_print:
            plugin._display_user_details(user_data)

        print_calls = [call[0][0] for call in mock_print.call_args_list]

        # Should show "None" when displayName is None based on the actual implementation
        assert any("👤 User Details: None" in call for call in print_calls)

    def test_display_user_details_header_and_formatting(self):
        """Test the output formatting of user details."""
        plugin = ViewUserPlugin()

        user_data = {
            "accountId": "12345",
            "displayName": "Test User",
            "emailAddress": "test@example.com",
            "active": True,
        }

        with patch("builtins.print") as mock_print:
            plugin._display_user_details(user_data)

        print_calls = [call[0][0] for call in mock_print.call_args_list]

        # Check header - first print includes newline and header together
        assert any("👤 User Details: Test User" in call for call in print_calls)
        assert any("=" * 50 in call for call in print_calls)

        # Check field formatting (dots between key and value)
        field_lines = [call for call in print_calls if "." in call]
        assert len(field_lines) > 0
        for line in field_lines:
            # Should have dots padding between key and value
            assert ".." in line

    def test_keys_to_drop_constant(self):
        """Test that keys_to_drop list is properly defined."""
        plugin = ViewUserPlugin()

        # Access the keys_to_drop from the method
        user_data = {
            "self": "url",
            "avatarUrls": {},
            "ownerId": "123",
            "applicationRoles": {},
            "groups": {},
            "expand": "groups",
            "accountId": "keep-this",
        }

        with patch("builtins.print") as mock_print:
            plugin._display_user_details(user_data)

        print_calls = [str(call) for call in mock_print.call_args_list]
        all_output = " ".join(print_calls).lower()

        # Verify dropped keys don't appear
        assert "self" not in all_output
        assert "avatarurls" not in all_output
        assert "ownerid" not in all_output
        assert "applicationroles" not in all_output
        assert "groups" not in all_output
        assert "expand" not in all_output

        # Verify kept key appears
        assert "accountid" in all_output or "keep-this" in all_output
