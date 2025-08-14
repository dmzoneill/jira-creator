#!/usr/bin/env python
"""Tests for the list sprints plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.plugins.list_sprints_plugin import ListSprintsPlugin


class TestListSprintsPlugin:
    """Test cases for ListSprintsPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = ListSprintsPlugin()
        assert plugin.command_name == "list-sprints"
        assert plugin.help_text == "List all sprints for a board"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = ListSprintsPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        assert mock_parser.add_argument.call_count == 1
        calls = mock_parser.add_argument.call_args_list

        # Check board-id argument
        assert calls[0][0] == ("-b", "--board-id")
        assert calls[0][1]["help"] == "Board ID (uses JIRA_BOARD_ID env var if not specified)"
        assert calls[0][1]["default"] is None

    def test_rest_operation_single_page(self):
        """Test REST operation with single page of results."""
        plugin = ListSprintsPlugin()
        mock_client = Mock()

        # Mock single page response
        mock_client.request.return_value = {
            "values": [
                {"id": 1, "name": "Sprint 1", "state": "closed"},
                {"id": 2, "name": "Sprint 2", "state": "active"},
                {"id": 3, "name": "Sprint 3", "state": "future"},
            ],
            "isLast": True,
        }

        result = plugin.rest_operation(mock_client, board_id="123")

        assert len(result) == 3
        assert result[0]["name"] == "Sprint 1"
        assert result[1]["name"] == "Sprint 2"
        assert result[2]["name"] == "Sprint 3"
        mock_client.request.assert_called_once_with("GET", "/rest/agile/1.0/board/123/sprint?startAt=0&maxResults=50")

    def test_rest_operation_multiple_pages(self):
        """Test REST operation with pagination."""
        plugin = ListSprintsPlugin()
        mock_client = Mock()

        # Create sprints for multiple pages
        first_page_sprints = [{"id": i, "name": f"Sprint {i}", "state": "closed"} for i in range(50)]
        second_page_sprints = [{"id": i, "name": f"Sprint {i}", "state": "active"} for i in range(50, 75)]

        # Mock paginated responses
        mock_client.request.side_effect = [
            {"values": first_page_sprints, "isLast": False},
            {"values": second_page_sprints, "isLast": True},
        ]

        result = plugin.rest_operation(mock_client, board_id="456")

        assert len(result) == 75
        assert result[0]["name"] == "Sprint 0"
        assert result[49]["name"] == "Sprint 49"
        assert result[50]["name"] == "Sprint 50"
        assert result[74]["name"] == "Sprint 74"

        # Verify pagination calls
        assert mock_client.request.call_count == 2
        calls = mock_client.request.call_args_list
        assert calls[0][0] == (
            "GET",
            "/rest/agile/1.0/board/456/sprint?startAt=0&maxResults=50",
        )
        assert calls[1][0] == (
            "GET",
            "/rest/agile/1.0/board/456/sprint?startAt=50&maxResults=50",
        )

    def test_rest_operation_empty_response(self):
        """Test REST operation with empty response."""
        plugin = ListSprintsPlugin()
        mock_client = Mock()

        # Mock empty response
        mock_client.request.return_value = {"values": [], "isLast": True}

        result = plugin.rest_operation(mock_client, board_id="789")

        assert result == []
        mock_client.request.assert_called_once()

    def test_rest_operation_less_than_max_results(self):
        """Test REST operation when results are less than maxResults."""
        plugin = ListSprintsPlugin()
        mock_client = Mock()

        # Mock response with less than 50 results
        mock_client.request.return_value = {
            "values": [
                {"id": 1, "name": "Sprint A", "state": "active"},
                {"id": 2, "name": "Sprint B", "state": "future"},
            ],
            "isLast": False,  # Even though isLast is False, we should stop
        }

        result = plugin.rest_operation(mock_client, board_id="999")

        assert len(result) == 2
        # Should only make one call since results < maxResults
        mock_client.request.assert_called_once()

    @patch("jira_creator.plugins.list_sprints_plugin.EnvFetcher.get")
    def test_execute_success_with_board_id_arg(self, mock_env_get, capsys):
        """Test successful execution with board ID from arguments."""
        plugin = ListSprintsPlugin()
        mock_client = Mock()

        # Mock sprint response
        mock_client.request.return_value = {
            "values": [
                {"id": 1, "name": "Sprint Alpha", "state": "closed"},
                {"id": 2, "name": "Sprint Beta", "state": "active"},
                {"id": 3, "name": "Sprint Gamma", "state": "future"},
            ],
            "isLast": True,
        }

        args = Namespace(board_id="111")

        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "📋 Sprints for board 111:" in captured.out
        assert "- Sprint Alpha (closed)" in captured.out
        assert "- Sprint Beta (active)" in captured.out
        assert "- Sprint Gamma (future)" in captured.out
        assert "Total: 3 sprints" in captured.out

        # Verify EnvFetcher was not called
        mock_env_get.assert_not_called()

    @patch("jira_creator.plugins.list_sprints_plugin.EnvFetcher.get")
    def test_execute_success_with_env_board_id(self, mock_env_get, capsys):
        """Test successful execution with board ID from environment."""
        plugin = ListSprintsPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "222"  # JIRA_BOARD_ID from env

        # Mock sprint response
        mock_client.request.return_value = {
            "values": [{"id": 10, "name": "Q1 Sprint", "state": "active"}],
            "isLast": True,
        }

        args = Namespace(board_id=None)

        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "📋 Sprints for board 222:" in captured.out
        assert "- Q1 Sprint (active)" in captured.out
        assert "Total: 1 sprints" in captured.out

    @patch("jira_creator.plugins.list_sprints_plugin.EnvFetcher.get")
    def test_execute_no_board_id(self, mock_env_get, capsys):
        """Test execution when no board ID is provided."""
        plugin = ListSprintsPlugin()
        mock_client = Mock()
        mock_env_get.return_value = None  # No JIRA_BOARD_ID

        args = Namespace(board_id=None)

        result = plugin.execute(mock_client, args)

        assert result is False
        captured = capsys.readouterr()
        assert "❌ No board ID specified. Use --board-id or set JIRA_BOARD_ID" in captured.out

    @patch("jira_creator.plugins.list_sprints_plugin.EnvFetcher.get")
    def test_execute_empty_sprints(self, mock_env_get, capsys):
        """Test execution when no sprints are found."""
        plugin = ListSprintsPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "333"

        # Mock empty response
        mock_client.request.return_value = {"values": [], "isLast": True}

        args = Namespace(board_id=None)

        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "📋 Sprints for board 333:" in captured.out
        assert "Total: 0 sprints" in captured.out

    @patch("jira_creator.plugins.list_sprints_plugin.EnvFetcher.get")
    def test_execute_with_unknown_state(self, mock_env_get, capsys):
        """Test execution when sprint has no state field."""
        plugin = ListSprintsPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "444"

        # Mock sprint response without state in some sprints
        mock_client.request.return_value = {
            "values": [
                {"id": 1, "name": "Sprint One"},  # No state
                {"id": 2, "name": "Sprint Two", "state": "active"},
            ],
            "isLast": True,
        }

        args = Namespace(board_id=None)

        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "- Sprint One (unknown)" in captured.out
        assert "- Sprint Two (active)" in captured.out

    @patch("jira_creator.plugins.list_sprints_plugin.EnvFetcher.get")
    def test_execute_with_exception(self, mock_env_get, capsys):
        """Test execution when an exception occurs."""
        plugin = ListSprintsPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "555"

        # Mock client to raise an exception
        mock_client.request.side_effect = RuntimeError("Network Error")

        args = Namespace(board_id=None)

        with pytest.raises(Exception) as exc_info:
            plugin.execute(mock_client, args)

        assert "Failed to list sprints: Network Error" in str(exc_info.value)
        captured = capsys.readouterr()
        assert "❌ Failed to list sprints: Network Error" in captured.out

    @patch("jira_creator.plugins.list_sprints_plugin.EnvFetcher.get")
    def test_execute_with_pagination(self, mock_env_get, capsys):
        """Test execution with paginated results."""
        plugin = ListSprintsPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "666"

        # Create many sprints requiring pagination
        page1_sprints = [{"id": i, "name": f"Sprint {i:02d}", "state": "closed"} for i in range(50)]
        page2_sprints = [{"id": i, "name": f"Sprint {i:02d}", "state": "active"} for i in range(50, 55)]

        mock_client.request.side_effect = [
            {"values": page1_sprints, "isLast": False},
            {"values": page2_sprints, "isLast": True},
        ]

        args = Namespace(board_id=None)

        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "📋 Sprints for board 666:" in captured.out
        # Check first and last sprints are printed
        assert "- Sprint 00 (closed)" in captured.out
        assert "- Sprint 54 (active)" in captured.out
        assert "Total: 55 sprints" in captured.out

    def test_rest_operation_no_values_key(self):
        """Test REST operation when response has no 'values' key."""
        plugin = ListSprintsPlugin()
        mock_client = Mock()

        # Mock response without 'values' key
        mock_client.request.return_value = {"isLast": True}

        result = plugin.rest_operation(mock_client, board_id="777")

        assert result == []

    def test_rest_operation_with_missing_isLast(self):
        """Test REST operation when response doesn't have isLast field."""
        plugin = ListSprintsPlugin()
        mock_client = Mock()

        # Mock response without isLast field (should default to False)
        mock_client.request.return_value = {"values": [{"id": 1, "name": "Sprint X", "state": "active"}]}

        result = plugin.rest_operation(mock_client, board_id="888")

        assert len(result) == 1
        # Should stop after one call since len(sprints) < max_results
        mock_client.request.assert_called_once()
