#!/usr/bin/env python
"""Tests for the set status plugin."""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import SetStatusError
from jira_creator.plugins.set_status_plugin import SetStatusPlugin


class TestSetStatusPlugin:
    """Test cases for SetStatusPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = SetStatusPlugin()
        assert plugin.command_name == "set-status"
        assert plugin.help_text == "Set the status of a Jira issue"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = SetStatusPlugin()
        mock_parser = Mock(spec=ArgumentParser)

        plugin.register_arguments(mock_parser)

        # Verify add_argument was called with correct parameters
        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list

        # First argument: issue_key
        assert calls[0][0] == ("issue_key",)
        assert calls[0][1]["help"] == "The Jira issue key (e.g., PROJ-123)"

        # Second argument: status
        assert calls[1][0] == ("status",)
        assert calls[1][1]["help"] == "The status to transition to"

    def test_get_transitions(self):
        """Test _get_transitions method."""
        plugin = SetStatusPlugin()
        mock_client = Mock()

        # Mock transitions response
        mock_transitions = {
            "transitions": [
                {"id": "11", "name": "To Do"},
                {"id": "21", "name": "In Progress"},
                {"id": "31", "name": "Done"},
            ]
        }
        mock_client.request.return_value = mock_transitions

        transitions = plugin._get_transitions(mock_client, "TEST-123")

        # Verify request
        mock_client.request.assert_called_once_with("GET", "/rest/api/2/issue/TEST-123/transitions")

        # Verify transitions returned
        assert transitions == mock_transitions["transitions"]

    def test_find_transition_id_exact_match(self):
        """Test _find_transition_id with exact match."""
        plugin = SetStatusPlugin()

        transitions = [
            {"id": "11", "name": "To Do"},
            {"id": "21", "name": "In Progress"},
            {"id": "31", "name": "Done"},
        ]

        # Test exact match (case insensitive)
        assert plugin._find_transition_id(transitions, "In Progress") == "21"
        assert plugin._find_transition_id(transitions, "in progress") == "21"
        assert plugin._find_transition_id(transitions, "IN PROGRESS") == "21"

    def test_find_transition_id_no_match(self):
        """Test _find_transition_id with no match."""
        plugin = SetStatusPlugin()

        transitions = [
            {"id": "11", "name": "To Do"},
            {"id": "21", "name": "In Progress"},
            {"id": "31", "name": "Done"},
        ]

        # Test no match
        assert plugin._find_transition_id(transitions, "Invalid Status") is None
        assert plugin._find_transition_id(transitions, "Closed") is None

    def test_rest_operation_success(self):
        """Test the REST operation with successful transition."""
        plugin = SetStatusPlugin()
        mock_client = Mock()

        # Mock transitions response
        mock_client.request.side_effect = [
            {  # GET transitions response
                "transitions": [
                    {"id": "11", "name": "To Do"},
                    {"id": "21", "name": "In Progress"},
                    {"id": "31", "name": "Done"},
                ]
            },
            {},  # POST transition response (empty)
        ]

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", status="Done")

        # Verify requests
        assert mock_client.request.call_count == 2
        calls = mock_client.request.call_args_list

        # First call: GET transitions
        assert calls[0][0] == ("GET", "/rest/api/2/issue/TEST-123/transitions")

        # Second call: POST transition
        assert calls[1][0] == ("POST", "/rest/api/2/issue/TEST-123/transitions")
        assert calls[1][1]["json_data"] == {"transition": {"id": "31"}}

        # Verify return value
        assert result == {}

    def test_rest_operation_status_not_available(self):
        """Test REST operation when status is not available."""
        plugin = SetStatusPlugin()
        mock_client = Mock()

        # Mock transitions response
        mock_client.request.return_value = {
            "transitions": [
                {"id": "11", "name": "To Do"},
                {"id": "21", "name": "In Progress"},
                {"id": "31", "name": "Done"},
            ]
        }

        with pytest.raises(SetStatusError) as exc_info:
            plugin.rest_operation(mock_client, issue_key="TEST-123", status="Closed")

        # Verify error message
        error_msg = str(exc_info.value)
        assert "Status 'Closed' not available" in error_msg
        assert "Available transitions: To Do, In Progress, Done" in error_msg

    def test_execute_success(self, capsys):
        """Test successful execution without refinement status."""
        plugin = SetStatusPlugin()
        mock_client = Mock()

        # Mock successful transition
        mock_client.request.side_effect = [
            {"transitions": [{"id": "21", "name": "In Progress"}]},  # GET transitions response
            {},  # POST transition response
        ]

        args = Namespace(issue_key="TEST-123", status="In Progress")

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Status set to 'In Progress'" in captured.out

    def test_execute_with_refinement_status(self, capsys):
        """Test execution with refinement status (special handling)."""
        plugin = SetStatusPlugin()
        mock_client = Mock()

        # Mock responses
        mock_client.request.side_effect = [
            {"transitions": [{"id": "41", "name": "Refinement"}]},  # GET transitions response
            {},  # POST transition response
            {},  # PUT rank to top response
            {"fields": {"parent": {"key": "EPIC-100"}}},  # GET issue details response
            {},  # PUT rank in epic response
        ]

        args = Namespace(issue_key="TEST-123", status="Refinement")

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True

        # Verify all expected calls were made
        assert mock_client.request.call_count == 5
        calls = mock_client.request.call_args_list

        # Verify ranking operations
        assert calls[2][0] == ("PUT", "/rest/greenhopper/1.0/sprint/rank")
        assert calls[2][1]["json_data"] == {
            "issueToMove": "TEST-123",
            "moveToTop": True,
        }

        assert calls[4][0] == ("PUT", "/rest/greenhopper/1.0/rank/global/first")
        assert calls[4][1]["json_data"] == {
            "issueToMove": "TEST-123",
            "parentKey": "EPIC-100",
        }

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Status set to 'Refinement'" in captured.out
        assert "📌 Moving issue to top of backlog..." in captured.out
        assert "📌 Moving issue to top of epic EPIC-100..." in captured.out

    def test_execute_refinement_status_no_epic(self, capsys):
        """Test refinement status when issue has no epic."""
        plugin = SetStatusPlugin()
        mock_client = Mock()

        # Mock responses
        mock_client.request.side_effect = [
            {"transitions": [{"id": "41", "name": "Refinement"}]},  # GET transitions response
            {},  # POST transition response
            {},  # PUT rank to top response
            {"fields": {}},  # GET issue details response (no parent)
        ]

        args = Namespace(issue_key="TEST-123", status="refinement")

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True

        # Should only make 4 calls (no epic ranking)
        assert mock_client.request.call_count == 4

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Status set to 'refinement'" in captured.out
        assert "📌 Moving issue to top of backlog..." in captured.out
        # Should not have epic ranking message
        assert "Moving issue to top of epic" not in captured.out

    def test_execute_refinement_with_ranking_failure(self, capsys):
        """Test refinement status when ranking operations fail."""
        plugin = SetStatusPlugin()
        mock_client = Mock()

        # Mock responses
        mock_client.request.side_effect = [
            {"transitions": [{"id": "41", "name": "Refinement"}]},  # GET transitions response
            {},  # POST transition response
            Exception("Ranking not allowed"),  # PUT rank fails
        ]

        args = Namespace(issue_key="TEST-123", status="Refinement")

        result = plugin.execute(mock_client, args)

        # Should still succeed (ranking is optional)
        assert result is True

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Status set to 'Refinement'" in captured.out
        assert "⚠️  Could not complete ranking operations: Ranking not allowed" in captured.out

    def test_execute_failure(self, capsys):
        """Test execution with API failure."""
        plugin = SetStatusPlugin()
        mock_client = Mock()

        # Mock transitions response that causes SetStatusError
        mock_client.request.return_value = {"transitions": []}  # No transitions available

        args = Namespace(issue_key="TEST-123", status="Done")

        # Verify exception is raised
        with pytest.raises(SetStatusError) as exc_info:
            plugin.execute(mock_client, args)

        # Verify the exception message
        assert "Status 'Done' not available" in str(exc_info.value)

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to set status:" in captured.out

    def test_handle_refinement_status_with_complex_epic_structure(self):
        """Test _handle_refinement_status with complex epic structure."""
        plugin = SetStatusPlugin()
        mock_client = Mock()

        # Mock responses with nested parent structure
        mock_client.request.side_effect = [
            {},  # PUT rank to top response
            {  # GET issue details response
                "fields": {"parent": {"key": "EPIC-200", "fields": {"summary": "Epic Summary"}}}
            },
            {},  # PUT rank in epic response
        ]

        plugin._handle_refinement_status(mock_client, "TEST-456")

        # Verify correct epic key was used
        epic_rank_call = mock_client.request.call_args_list[2]
        assert epic_rank_call[1]["json_data"]["parentKey"] == "EPIC-200"

    def test_execute_with_various_status_names(self):
        """Test execution with various status names."""
        plugin = SetStatusPlugin()
        mock_client = Mock()

        test_statuses = [
            "To Do",
            "In Progress",
            "Code Review",
            "Testing",
            "Done",
            "Won't Fix",
            "Blocked",
        ]

        for status in test_statuses:
            mock_client.reset_mock()

            # Mock successful transition
            mock_client.request.side_effect = [
                {"transitions": [{"id": "99", "name": status}]},  # GET transitions response
                {},  # POST transition response
            ]

            args = Namespace(issue_key="TEST-123", status=status)

            result = plugin.execute(mock_client, args)

            assert result is True

    def test_rest_operation_empty_transitions(self):
        """Test REST operation when no transitions are available."""
        plugin = SetStatusPlugin()
        mock_client = Mock()

        # Mock empty transitions response
        mock_client.request.return_value = {"transitions": []}

        with pytest.raises(SetStatusError) as exc_info:
            plugin.rest_operation(mock_client, issue_key="TEST-123", status="Any Status")

        # Verify error message
        error_msg = str(exc_info.value)
        assert "Status 'Any Status' not available" in error_msg
        assert "Available transitions: " in error_msg  # Empty list

    def test_case_insensitive_status_matching(self):
        """Test that status matching is case insensitive."""
        plugin = SetStatusPlugin()
        mock_client = Mock()

        # Mock transitions with mixed case
        mock_client.request.side_effect = [
            {  # GET transitions response
                "transitions": [
                    {"id": "11", "name": "To Do"},
                    {"id": "21", "name": "IN PROGRESS"},
                    {"id": "31", "name": "done"},
                ]
            },
            {},  # POST transition response
        ]

        # Test with different case
        plugin.rest_operation(mock_client, issue_key="TEST-123", status="iN pRoGrEsS")

        # Verify correct transition ID was used
        post_call = mock_client.request.call_args_list[1]
        assert post_call[1]["json_data"]["transition"]["id"] == "21"
