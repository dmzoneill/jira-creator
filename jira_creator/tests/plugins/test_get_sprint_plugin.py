#!/usr/bin/env python
"""Tests for the get sprint plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.plugins.get_sprint_plugin import GetSprintPlugin


class TestGetSprintPlugin:
    """Test cases for GetSprintPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = GetSprintPlugin()
        assert plugin.command_name == "get-sprint"
        assert plugin.help_text == "Get the current active sprint"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = GetSprintPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        assert mock_parser.add_argument.call_count == 1
        calls = mock_parser.add_argument.call_args_list

        # Check board-id argument
        assert calls[0][0] == ("-b", "--board-id")
        assert calls[0][1]["help"] == "Board ID (uses JIRA_BOARD_ID env var if not specified)"
        assert calls[0][1]["default"] is None

    def test_rest_operation(self):
        """Test REST operation."""
        plugin = GetSprintPlugin()
        mock_client = Mock()

        expected_response = {
            "values": [
                {
                    "id": 123,
                    "name": "Sprint 1",
                    "state": "active",
                    "startDate": "2024-01-01T00:00:00.000Z",
                    "endDate": "2024-01-14T00:00:00.000Z",
                }
            ]
        }
        mock_client.request.return_value = expected_response

        result = plugin.rest_operation(mock_client, board_id="456")

        assert result == expected_response
        mock_client.request.assert_called_once_with("GET", "/rest/agile/1.0/board/456/sprint?state=active")

    @patch("jira_creator.plugins.get_sprint_plugin.EnvFetcher.get")
    def test_execute_success_with_board_id_arg(self, mock_env_get, capsys):
        """Test successful execution with board ID from arguments."""
        plugin = GetSprintPlugin()
        mock_client = Mock()

        # Mock sprint response
        mock_client.request.return_value = {
            "values": [
                {
                    "id": 123,
                    "name": "Sprint 2024.01",
                    "state": "active",
                    "startDate": "2024-01-01T00:00:00.000Z",
                    "endDate": "2024-01-14T23:59:59.000Z",
                }
            ]
        }

        args = Namespace(board_id="789")

        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "🏃 Active Sprint: Sprint 2024.01" in captured.out
        assert "State: active" in captured.out
        assert "ID: 123" in captured.out
        assert "Start: 2024-01-01" in captured.out
        assert "End: 2024-01-14" in captured.out

        # Verify EnvFetcher was not called
        mock_env_get.assert_not_called()

    @patch("jira_creator.plugins.get_sprint_plugin.EnvFetcher.get")
    def test_execute_success_with_env_board_id(self, mock_env_get, capsys):
        """Test successful execution with board ID from environment."""
        plugin = GetSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "999"  # JIRA_BOARD_ID from env

        # Mock sprint response
        mock_client.request.return_value = {
            "values": [
                {
                    "id": 456,
                    "name": "Sprint Beta",
                    "state": "active",
                    # No dates provided
                }
            ]
        }

        args = Namespace(board_id=None)

        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "🏃 Active Sprint: Sprint Beta" in captured.out
        assert "State: active" in captured.out
        assert "ID: 456" in captured.out
        # Dates should not be printed if not provided
        assert "Start:" not in captured.out
        assert "End:" not in captured.out

    @patch("jira_creator.plugins.get_sprint_plugin.EnvFetcher.get")
    def test_execute_no_board_id(self, mock_env_get, capsys):
        """Test execution when no board ID is provided."""
        plugin = GetSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = None  # No JIRA_BOARD_ID

        args = Namespace(board_id=None)

        result = plugin.execute(mock_client, args)

        assert result is False
        captured = capsys.readouterr()
        assert "❌ No board ID specified. Use --board-id or set JIRA_BOARD_ID" in captured.out

    @patch("jira_creator.plugins.get_sprint_plugin.EnvFetcher.get")
    def test_execute_no_active_sprint(self, mock_env_get, capsys):
        """Test execution when no active sprint is found."""
        plugin = GetSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "123"

        # Mock empty response
        mock_client.request.return_value = {"values": []}

        args = Namespace(board_id=None)

        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "📭 No active sprint found" in captured.out

    @patch("jira_creator.plugins.get_sprint_plugin.EnvFetcher.get")
    def test_execute_with_null_values(self, mock_env_get, capsys):
        """Test execution when sprint data contains null values."""
        plugin = GetSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "123"

        # Mock response with null values
        mock_client.request.return_value = None

        args = Namespace(board_id=None)

        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "📭 No active sprint found" in captured.out

    @patch("jira_creator.plugins.get_sprint_plugin.EnvFetcher.get")
    def test_execute_with_exception(self, mock_env_get, capsys):
        """Test execution when an exception occurs."""
        plugin = GetSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "123"

        # Mock client to raise an exception
        mock_client.request.side_effect = RuntimeError("API Error")

        args = Namespace(board_id=None)

        with pytest.raises(Exception) as exc_info:
            plugin.execute(mock_client, args)

        assert "Failed to get sprint: API Error" in str(exc_info.value)
        captured = capsys.readouterr()
        assert "❌ Failed to get sprint: API Error" in captured.out

    @patch("jira_creator.plugins.get_sprint_plugin.EnvFetcher.get")
    def test_execute_with_unknown_state(self, mock_env_get, capsys):
        """Test execution when sprint has no state field."""
        plugin = GetSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "123"

        # Mock sprint response without state
        mock_client.request.return_value = {
            "values": [
                {
                    "id": 789,
                    "name": "Sprint Unknown",
                    # No state field
                }
            ]
        }

        args = Namespace(board_id=None)

        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "🏃 Active Sprint: Sprint Unknown" in captured.out
        assert "State: Unknown" in captured.out
        assert "ID: 789" in captured.out

    @patch("jira_creator.plugins.get_sprint_plugin.EnvFetcher.get")
    def test_execute_with_partial_dates(self, mock_env_get, capsys):
        """Test execution when sprint has only start date."""
        plugin = GetSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "123"

        # Mock sprint response with only start date
        mock_client.request.return_value = {
            "values": [
                {
                    "id": 321,
                    "name": "Sprint Partial",
                    "state": "active",
                    "startDate": "2024-02-15T10:30:00.000Z",
                    # No end date
                }
            ]
        }

        args = Namespace(board_id=None)

        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "Start: 2024-02-15" in captured.out
        assert "End:" not in captured.out
