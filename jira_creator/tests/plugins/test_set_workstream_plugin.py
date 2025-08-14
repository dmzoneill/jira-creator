#!/usr/bin/env python
"""Tests for the set workstream plugin."""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import SetWorkstreamError
from jira_creator.plugins.set_workstream_plugin import SetWorkstreamPlugin


class TestSetWorkstreamPlugin:
    """Test cases for SetWorkstreamPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = SetWorkstreamPlugin()
        assert plugin.command_name == "set-workstream"
        assert plugin.help_text == "Set the workstream of a Jira issue"
        assert plugin.field_name == "workstream"
        assert plugin.argument_name == "workstream_id"
        assert plugin.argument_help == "The workstream ID (optional, uses default if not provided)"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = SetWorkstreamPlugin()
        mock_parser = Mock(spec=ArgumentParser)

        # Create mock for _positionals
        mock_positionals = Mock()
        mock_positionals._actions = []
        mock_parser._positionals = mock_positionals

        plugin.register_arguments(mock_parser)

        # Verify add_argument was called with correct parameters
        assert mock_parser.add_argument.call_count == 3
        calls = mock_parser.add_argument.call_args_list

        # First argument: issue_key
        assert calls[0][0] == ("issue_key",)
        assert calls[0][1]["help"] == "The Jira issue key (e.g., PROJ-123)"

        # Second argument: workstream_id (positional, will be filtered out later)
        assert calls[1][0] == ("workstream_id",)

        # Third argument: --workstream-id (optional)
        assert calls[2][0] == ("--workstream-id",)
        assert calls[2][1]["dest"] == "workstream_id"
        assert calls[2][1]["help"] == "The workstream ID (optional, uses default if not provided)"
        assert calls[2][1]["default"] is None

    def test_register_additional_arguments(self):
        """Test register_additional_arguments modifies parser correctly."""
        plugin = SetWorkstreamPlugin()
        mock_parser = Mock(spec=ArgumentParser)

        # Create mock for _positionals with an action for 'workstream_id'
        mock_action = Mock()
        mock_action.dest = "workstream_id"
        mock_positionals = Mock()
        mock_positionals._actions = [mock_action]
        mock_parser._positionals = mock_positionals

        plugin.register_additional_arguments(mock_parser)

        # Verify the action was removed
        assert len(mock_parser._positionals._actions) == 0

        # Verify add_argument was called for --workstream-id
        mock_parser.add_argument.assert_called_once_with(
            "--workstream-id",
            dest="workstream_id",
            help="The workstream ID (optional, uses default if not provided)",
            default=None,
        )

    @patch("jira_creator.plugins.set_workstream_plugin.EnvFetcher")
    def test_rest_operation(self, mock_env_fetcher):
        """Test the REST operation directly."""
        plugin = SetWorkstreamPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        # Mock EnvFetcher.get to return workstream field
        mock_env_fetcher.get.return_value = "customfield_10020"

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", value="WS-123")

        # Verify EnvFetcher was called for field only
        mock_env_fetcher.get.assert_called_once_with("JIRA_WORKSTREAM_FIELD")

        # Verify the request
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10020": [{"id": "WS-123"}]}},
        )
        assert result == {"key": "TEST-123"}

    @patch("jira_creator.plugins.set_workstream_plugin.EnvFetcher")
    def test_rest_operation_with_default(self, mock_env_fetcher):
        """Test REST operation when no workstream ID provided (uses default)."""
        plugin = SetWorkstreamPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        # Mock EnvFetcher.get to return field and default ID
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_WORKSTREAM_FIELD": "customfield_10020",
            "JIRA_WORKSTREAM_ID": "WS-DEFAULT",
        }.get(key)

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", value=None)

        # Verify EnvFetcher was called for both field and default ID
        assert mock_env_fetcher.get.call_count == 2
        mock_env_fetcher.get.assert_any_call("JIRA_WORKSTREAM_FIELD")
        mock_env_fetcher.get.assert_any_call("JIRA_WORKSTREAM_ID")

        # Verify the request uses default ID
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10020": [{"id": "WS-DEFAULT"}]}},
        )
        assert result == {"key": "TEST-123"}

    @patch("jira_creator.plugins.set_workstream_plugin.EnvFetcher")
    def test_execute_success_with_id(self, mock_env_fetcher, capsys):
        """Test successful execution with provided workstream ID."""
        plugin = SetWorkstreamPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        mock_env_fetcher.get.return_value = "customfield_10020"

        args = Namespace(issue_key="TEST-123", workstream_id="WS-456")

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10020": [{"id": "WS-456"}]}},
        )

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Workstream set to ID 'WS-456'" in captured.out

    @patch("jira_creator.plugins.set_workstream_plugin.EnvFetcher")
    def test_execute_success_with_default(self, mock_env_fetcher, capsys):
        """Test successful execution using default workstream ID."""
        plugin = SetWorkstreamPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        # Mock EnvFetcher.get to return field and default ID
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_WORKSTREAM_FIELD": "customfield_10020",
            "JIRA_WORKSTREAM_ID": "WS-DEFAULT",
        }.get(key)

        args = Namespace(issue_key="TEST-123", workstream_id=None)

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10020": [{"id": "WS-DEFAULT"}]}},
        )

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Workstream set to default value" in captured.out

    @patch("jira_creator.plugins.set_workstream_plugin.EnvFetcher")
    def test_execute_failure(self, mock_env_fetcher, capsys):
        """Test execution with API failure."""
        plugin = SetWorkstreamPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = SetWorkstreamError("Invalid workstream ID")

        mock_env_fetcher.get.return_value = "customfield_10020"

        args = Namespace(issue_key="TEST-123", workstream_id="INVALID-WS")

        # Verify exception is raised
        with pytest.raises(SetWorkstreamError) as exc_info:
            plugin.execute(mock_client, args)

        # Verify the exception message
        assert str(exc_info.value) == "Invalid workstream ID"

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to set workstream: Invalid workstream ID" in captured.out

    @patch("jira_creator.plugins.set_workstream_plugin.EnvFetcher")
    def test_format_success_message(self, mock_env_fetcher):
        """Test format_success_message method for different cases."""
        plugin = SetWorkstreamPlugin()

        # Test with value
        msg = plugin.format_success_message("TEST-123", "WS-789")
        assert msg == "✅ Workstream set to ID 'WS-789'"

        # Test without value (default)
        msg = plugin.format_success_message("TEST-123", None)
        assert msg == "✅ Workstream set to default value"

        # Test with empty string
        msg = plugin.format_success_message("TEST-123", "")
        assert msg == "✅ Workstream set to default value"

    @patch("jira_creator.plugins.set_workstream_plugin.EnvFetcher")
    def test_execute_with_different_workstream_ids(self, mock_env_fetcher):
        """Test execute with different workstream ID formats."""
        plugin = SetWorkstreamPlugin()
        mock_client = Mock()
        mock_env_fetcher.get.return_value = "customfield_10020"

        # Test different workstream ID formats
        test_ids = [
            "WS-001",
            "WORKSTREAM-123",
            "12345",  # Numeric ID
            "team-alpha",  # String ID
            "PROD_WORKSTREAM",
        ]

        for ws_id in test_ids:
            mock_client.reset_mock()
            args = Namespace(issue_key="TEST-123", workstream_id=ws_id)

            result = plugin.execute(mock_client, args)

            assert result is True
            # Verify the workstream ID was passed correctly
            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["fields"]["customfield_10020"] == [{"id": ws_id}]

    @patch("jira_creator.plugins.set_workstream_plugin.EnvFetcher")
    def test_rest_operation_payload_structure(self, mock_env_fetcher):
        """Test that REST operation creates correct payload structure."""
        plugin = SetWorkstreamPlugin()
        mock_client = Mock()
        mock_env_fetcher.get.return_value = "customfield_10020"

        plugin.rest_operation(mock_client, issue_key="TEST-456", value="WS-789")

        # Verify the payload structure (workstream is an array with id object)
        call_args = mock_client.request.call_args[1]["json_data"]
        assert "fields" in call_args
        assert "customfield_10020" in call_args["fields"]
        assert isinstance(call_args["fields"]["customfield_10020"], list)
        assert len(call_args["fields"]["customfield_10020"]) == 1
        assert call_args["fields"]["customfield_10020"][0] == {"id": "WS-789"}

    @patch("jira_creator.plugins.set_workstream_plugin.EnvFetcher")
    def test_env_fetcher_returns_different_field(self, mock_env_fetcher):
        """Test that the plugin uses the field returned by EnvFetcher."""
        plugin = SetWorkstreamPlugin()
        mock_client = Mock()

        # Test with different custom field IDs
        custom_fields = ["customfield_10020", "customfield_30030", "workstream_field"]

        for field_id in custom_fields:
            mock_client.reset_mock()
            mock_env_fetcher.get.side_effect = lambda key: {
                "JIRA_WORKSTREAM_FIELD": field_id,
            }.get(key)

            plugin.rest_operation(mock_client, issue_key="TEST-123", value="WS-999")

            # Verify the correct field ID was used
            call_args = mock_client.request.call_args[1]["json_data"]
            assert field_id in call_args["fields"]
            assert call_args["fields"][field_id] == [{"id": "WS-999"}]

    @patch("jira_creator.plugins.set_workstream_plugin.EnvFetcher")
    def test_execute_with_empty_string_workstream_id(self, mock_env_fetcher, capsys):
        """Test execution with empty string workstream ID (should use default)."""
        plugin = SetWorkstreamPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        # Mock EnvFetcher.get to return field and default ID
        mock_env_fetcher.get.side_effect = lambda key: {
            "JIRA_WORKSTREAM_FIELD": "customfield_10020",
            "JIRA_WORKSTREAM_ID": "WS-DEFAULT",
        }.get(key)

        args = Namespace(issue_key="TEST-123", workstream_id="")

        result = plugin.execute(mock_client, args)

        # Verify it uses the default
        assert result is True
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10020": [{"id": "WS-DEFAULT"}]}},
        )

        # Verify print output shows default was used
        captured = capsys.readouterr()
        assert "✅ Workstream set to default value" in captured.out
