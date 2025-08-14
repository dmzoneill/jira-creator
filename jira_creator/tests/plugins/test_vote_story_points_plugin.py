#!/usr/bin/env python
"""Tests for the vote story points plugin."""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import FetchIssueIDError, VoteStoryPointsError
from jira_creator.plugins.vote_story_points_plugin import VoteStoryPointsPlugin


class TestVoteStoryPointsPlugin:
    """Test cases for VoteStoryPointsPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = VoteStoryPointsPlugin()
        assert plugin.command_name == "vote-story-points"
        assert plugin.help_text == "Vote on story points"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = VoteStoryPointsPlugin()
        mock_parser = Mock(spec=ArgumentParser)

        plugin.register_arguments(mock_parser)

        # Verify add_argument was called with correct parameters
        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list

        # First argument: issue_key
        assert calls[0][0] == ("issue_key",)
        assert calls[0][1]["help"] == "The Jira issue id/key"

        # Second argument: points
        assert calls[1][0] == ("points",)
        assert calls[1][1]["help"] == "Number of story points to vote"

    def test_rest_operation_success(self):
        """Test the REST operation directly with successful response."""
        plugin = VoteStoryPointsPlugin()
        mock_client = Mock()

        # Mock the GET request to fetch issue ID
        mock_client.request.side_effect = [
            {"id": "12345", "key": "TEST-123"},  # GET issue response
            {"success": True},  # PUT vote response
        ]

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", points=5)

        # Verify the requests
        assert mock_client.request.call_count == 2

        # First call: GET issue
        calls = mock_client.request.call_args_list
        assert calls[0][0] == ("GET", "/rest/api/2/issue/TEST-123")

        # Second call: PUT vote
        assert calls[1][0] == ("PUT", "/rest/eausm/latest/planningPoker/vote")
        assert calls[1][1]["json_data"] == {"issueId": "12345", "vote": 5}

        # Verify return value
        assert result == {"success": True, "issue_key": "TEST-123", "points": 5}

    def test_rest_operation_fetch_issue_failure(self):
        """Test REST operation when fetching issue ID fails."""
        plugin = VoteStoryPointsPlugin()
        mock_client = Mock()

        # Mock the GET request to fail
        mock_client.request.side_effect = Exception("404 Not Found")

        with pytest.raises(FetchIssueIDError) as exc_info:
            plugin.rest_operation(mock_client, issue_key="INVALID-999", points=3)

        # Verify the error message
        assert "Failed to fetch issue ID for INVALID-999" in str(exc_info.value)
        assert "404 Not Found" in str(exc_info.value)

    def test_rest_operation_vote_failure(self):
        """Test REST operation when voting fails."""
        plugin = VoteStoryPointsPlugin()
        mock_client = Mock()

        # Mock successful GET but failed PUT
        mock_client.request.side_effect = [
            {"id": "12345", "key": "TEST-123"},  # GET issue response
            Exception("Permission denied"),  # PUT vote fails
        ]

        with pytest.raises(VoteStoryPointsError) as exc_info:
            plugin.rest_operation(mock_client, issue_key="TEST-123", points=8)

        # Verify the error message
        assert "Failed to vote on story points: Permission denied" in str(exc_info.value)

    def test_execute_success(self, capsys):
        """Test successful execution."""
        plugin = VoteStoryPointsPlugin()
        mock_client = Mock()

        # Mock successful responses
        mock_client.request.side_effect = [
            {"id": "12345", "key": "TEST-123"},  # GET issue response
            {"success": True},  # PUT vote response
        ]

        args = Namespace(issue_key="TEST-123", points="5")

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Voted 5 points on TEST-123" in captured.out

    def test_execute_invalid_points(self, capsys):
        """Test execution with invalid points value."""
        plugin = VoteStoryPointsPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", points="invalid")

        result = plugin.execute(mock_client, args)

        # Verify failure
        assert result is False

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Story points must be an integer." in captured.out

        # Verify no API calls were made
        mock_client.request.assert_not_called()

    def test_execute_with_vote_error(self, capsys):
        """Test execution with voting error."""
        plugin = VoteStoryPointsPlugin()
        mock_client = Mock()

        # Mock successful GET but failed PUT
        mock_client.request.side_effect = [
            {"id": "12345", "key": "TEST-123"},  # GET issue response
            Exception("Voting not allowed"),  # PUT vote fails
        ]

        args = Namespace(issue_key="TEST-123", points="13")

        # Verify exception is raised
        with pytest.raises(VoteStoryPointsError) as exc_info:
            plugin.execute(mock_client, args)

        # Verify the exception message
        assert "Voting not allowed" in str(exc_info.value)

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to vote on story points:" in captured.out

    def test_execute_with_different_point_values(self):
        """Test execute with different story point values."""
        plugin = VoteStoryPointsPlugin()
        mock_client = Mock()

        # Common Fibonacci sequence values used for story points
        test_points = ["1", "2", "3", "5", "8", "13", "21", "34"]

        for points_str in test_points:
            mock_client.reset_mock()

            # Mock successful responses
            mock_client.request.side_effect = [
                {"id": "12345", "key": "TEST-123"},  # GET issue response
                {"success": True},  # PUT vote response
            ]

            args = Namespace(issue_key="TEST-123", points=points_str)

            result = plugin.execute(mock_client, args)

            assert result is True

            # Verify the correct points value was sent
            vote_call = mock_client.request.call_args_list[1]
            assert vote_call[1]["json_data"]["vote"] == int(points_str)

    def test_execute_with_zero_points(self, capsys):
        """Test execution with zero points."""
        plugin = VoteStoryPointsPlugin()
        mock_client = Mock()

        # Mock successful responses
        mock_client.request.side_effect = [
            {"id": "12345", "key": "TEST-123"},  # GET issue response
            {"success": True},  # PUT vote response
        ]

        args = Namespace(issue_key="TEST-123", points="0")

        result = plugin.execute(mock_client, args)

        # Verify success (0 is a valid integer)
        assert result is True

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Voted 0 points on TEST-123" in captured.out

    def test_execute_with_negative_points(self, capsys):
        """Test execution with negative points."""
        plugin = VoteStoryPointsPlugin()
        mock_client = Mock()

        # Mock successful responses
        mock_client.request.side_effect = [
            {"id": "12345", "key": "TEST-123"},  # GET issue response
            {"success": True},  # PUT vote response
        ]

        args = Namespace(issue_key="TEST-123", points="-5")

        result = plugin.execute(mock_client, args)

        # Verify success (negative is still a valid integer)
        assert result is True

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Voted -5 points on TEST-123" in captured.out

    def test_rest_operation_with_different_issue_keys(self):
        """Test REST operation with various issue key formats."""
        plugin = VoteStoryPointsPlugin()
        mock_client = Mock()

        test_cases = [
            ("PROJ-123", "54321"),
            ("ABC-1", "10001"),
            ("LONGPROJECT-99999", "99999"),
        ]

        for issue_key, issue_id in test_cases:
            mock_client.reset_mock()

            # Mock successful responses
            mock_client.request.side_effect = [
                {"id": issue_id, "key": issue_key},  # GET issue response
                {"success": True},  # PUT vote response
            ]

            result = plugin.rest_operation(mock_client, issue_key=issue_key, points=5)

            # Verify the issue ID was used correctly
            vote_call = mock_client.request.call_args_list[1]
            assert vote_call[1]["json_data"]["issueId"] == issue_id
            assert result["issue_key"] == issue_key

    def test_execute_with_string_number_with_spaces(self, capsys):
        """Test execution with string number containing spaces."""
        plugin = VoteStoryPointsPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", points=" 5 ")

        # Mock successful responses
        mock_client.request.side_effect = [
            {"id": "12345", "key": "TEST-123"},  # GET issue response
            {"success": True},  # PUT vote response
        ]

        result = plugin.execute(mock_client, args)

        # Should succeed as int() can handle spaces
        assert result is True

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Voted 5 points on TEST-123" in captured.out

    def test_execute_with_float_string(self, capsys):
        """Test execution with float string (should fail)."""
        plugin = VoteStoryPointsPlugin()
        mock_client = Mock()

        args = Namespace(issue_key="TEST-123", points="5.5")

        result = plugin.execute(mock_client, args)

        # Should fail as int() cannot convert float string
        assert result is False

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Story points must be an integer." in captured.out
