#!/usr/bin/env python
"""Tests for the add to sprint plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import AddSprintError
from jira_creator.plugins.add_to_sprint_plugin import AddToSprintPlugin


class TestAddToSprintPlugin:
    """Test cases for AddToSprintPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = AddToSprintPlugin()
        assert plugin.command_name == "add-to-sprint"
        assert plugin.help_text == "Add an issue to a sprint and optionally assign it"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = AddToSprintPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        assert mock_parser.add_argument.call_count == 3
        calls = mock_parser.add_argument.call_args_list

        # Check issue_key argument
        assert calls[0][0][0] == "issue_key"
        assert calls[0][1]["help"] == "The Jira issue key (e.g., PROJ-123)"

        # Check sprint_name argument
        assert calls[1][0][0] == "sprint_name"
        assert calls[1][1]["help"] == "The name of the sprint"

        # Check assignee argument
        assert calls[2][0] == ("-a", "--assignee")
        assert calls[2][1]["help"] == "Assignee username (defaults to current user if not specified)"
        assert calls[2][1]["default"] is None

    @patch("jira_creator.plugins.add_to_sprint_plugin.EnvFetcher.get")
    def test_rest_operation_with_assignee(self, mock_env_get):
        """Test REST operation with specified assignee."""
        plugin = AddToSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "123"  # JIRA_BOARD_ID

        # Mock sprint search response
        mock_client.request.side_effect = [
            {
                "values": [{"id": 456, "name": "Sprint 1"}],
                "isLast": True,
            },  # Sprint search
            None,  # Assign issue
            {"success": True},  # Add to sprint
        ]

        result = plugin.rest_operation(
            mock_client,
            issue_key="TEST-123",
            sprint_name="Sprint 1",
            assignee="john.doe",
        )

        assert result == {"success": True}
        assert mock_client.request.call_count == 3

        # Verify assign call
        assign_call = mock_client.request.call_args_list[1]
        assert assign_call[0] == ("PUT", "/rest/api/2/issue/TEST-123")
        assert assign_call[1]["json_data"] == {"fields": {"assignee": {"name": "john.doe"}}}

    @patch("jira_creator.plugins.add_to_sprint_plugin.EnvFetcher.get")
    def test_rest_operation_without_assignee(self, mock_env_get):
        """Test REST operation without assignee (defaults to current user)."""
        plugin = AddToSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "123"  # JIRA_BOARD_ID

        # Mock responses
        mock_client.request.side_effect = [
            {
                "values": [{"id": 456, "name": "Sprint 1"}],
                "isLast": True,
            },  # Sprint search
            {"name": "current.user"},  # Get current user
            None,  # Assign issue
            {"success": True},  # Add to sprint
        ]

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", sprint_name="Sprint 1", assignee=None)

        assert result == {"success": True}
        assert mock_client.request.call_count == 4

        # Verify current user was fetched
        user_call = mock_client.request.call_args_list[1]
        assert user_call[0] == ("GET", "/rest/api/2/myself")

    @patch("jira_creator.plugins.add_to_sprint_plugin.EnvFetcher.get")
    def test_rest_operation_no_board_id(self, mock_env_get):
        """Test REST operation when JIRA_BOARD_ID is not set."""
        plugin = AddToSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = None

        with pytest.raises(AddSprintError) as exc_info:
            plugin.rest_operation(
                mock_client,
                issue_key="TEST-123",
                sprint_name="Sprint 1",
                assignee="john.doe",
            )

        assert "JIRA_BOARD_ID not set in environment" in str(exc_info.value)

    @patch("jira_creator.plugins.add_to_sprint_plugin.EnvFetcher.get")
    def test_rest_operation_sprint_not_found(self, mock_env_get):
        """Test REST operation when sprint is not found."""
        plugin = AddToSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "123"

        # Mock empty sprint search response
        mock_client.request.return_value = {"values": [], "isLast": True}

        with pytest.raises(AddSprintError) as exc_info:
            plugin.rest_operation(
                mock_client,
                issue_key="TEST-123",
                sprint_name="Nonexistent Sprint",
                assignee="john.doe",
            )

        assert "Could not find sprint named 'Nonexistent Sprint'" in str(exc_info.value)

    def test_find_sprint_id_found(self):
        """Test _find_sprint_id when sprint is found."""
        plugin = AddToSprintPlugin()
        mock_client = Mock()

        mock_client.request.return_value = {
            "values": [
                {"id": 100, "name": "Sprint A"},
                {"id": 200, "name": "Sprint B"},
                {"id": 300, "name": "Sprint C"},
            ],
            "isLast": True,
        }

        sprint_id = plugin._find_sprint_id(mock_client, "123", "Sprint B")

        assert sprint_id == 200

    def test_find_sprint_id_pagination(self):
        """Test _find_sprint_id with pagination."""
        plugin = AddToSprintPlugin()
        mock_client = Mock()

        # Create sprints to fill pages (50 per page by default)
        first_page_sprints = [{"id": i, "name": f"Sprint {i}"} for i in range(50)]
        second_page_sprints = [
            {"id": 200, "name": "Sprint B"},
            {"id": 201, "name": "Sprint C"},
        ]

        # Create a list of responses for side_effect
        responses = [
            {"values": first_page_sprints, "isLast": False},
            {"values": second_page_sprints, "isLast": True},
        ]
        mock_client.request.side_effect = responses

        sprint_id = plugin._find_sprint_id(mock_client, "123", "Sprint B")

        assert sprint_id == 200
        assert mock_client.request.call_count == 2

    def test_find_sprint_id_not_found(self):
        """Test _find_sprint_id when sprint is not found."""
        plugin = AddToSprintPlugin()
        mock_client = Mock()

        mock_client.request.return_value = {"values": [], "isLast": True}

        sprint_id = plugin._find_sprint_id(mock_client, "123", "Nonexistent")

        assert sprint_id is None

    @patch("jira_creator.plugins.add_to_sprint_plugin.EnvFetcher.get")
    def test_execute_success(self, mock_env_get, capsys):
        """Test successful execution."""
        plugin = AddToSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "123"

        # Mock successful responses
        mock_client.request.side_effect = [
            {"values": [{"id": 456, "name": "Sprint 1"}], "isLast": True},
            None,  # Assign
            {"success": True},  # Add to sprint
        ]

        args = Namespace(issue_key="TEST-123", sprint_name="Sprint 1", assignee="john.doe")

        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "✅ Added to sprint 'Sprint 1'" in captured.out

    @patch("jira_creator.plugins.add_to_sprint_plugin.EnvFetcher.get")
    def test_execute_failure(self, mock_env_get, capsys):
        """Test execution with AddSprintError."""
        plugin = AddToSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = None  # Will cause error

        args = Namespace(issue_key="TEST-123", sprint_name="Sprint 1", assignee="john.doe")

        with pytest.raises(AddSprintError):
            plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "❌" in captured.out

    @patch("jira_creator.plugins.add_to_sprint_plugin.EnvFetcher.get")
    def test_rest_operation_prints_success(self, mock_env_get, capsys):
        """Test that REST operation prints success message."""
        plugin = AddToSprintPlugin()
        mock_client = Mock()
        mock_env_get.return_value = "123"

        mock_client.request.side_effect = [
            {"values": [{"id": 456, "name": "Sprint 1"}], "isLast": True},
            None,
            {"success": True},
        ]

        plugin.rest_operation(
            mock_client,
            issue_key="TEST-123",
            sprint_name="Sprint 1",
            assignee="john.doe",
        )

        captured = capsys.readouterr()
        assert "✅ Added TEST-123 to sprint 'Sprint 1' on board 123" in captured.out
