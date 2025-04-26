#!/usr/bin/env python
"""
This module contains unit tests for the `vote_story_points` method within a client class that interacts with an API for
voting on story points associated with issues.

The tests validate scenarios such as successful voting, handling failures during the voting process, and managing
errors when fetching the issue ID required for voting.

Functions:
- `test_vote_story_points_success(client)`: Tests successful voting of story points, ensuring correct API calls.
- `test_vote_story_points_failure(client, capsys)`: Tests failure scenarios for voting, verifying error handling and
output.
- `test_vote_story_points_fetch_issue_id_failure(client, capsys)`: Tests failure to fetch the issue ID, ensuring proper
exception handling and output.

Mock objects are utilized to simulate API responses and exceptions, allowing for isolated testing of the voting
functionality without actual API calls.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import FetchIssueIDError, VoteStoryPointsError


def test_vote_story_points_success(client):
    """
    Retrieve the issue ID for voting on story points.

    Arguments:
    - client: A client object used to make API requests.
    """

    # First call: get issue ID
    mock_issue_response = MagicMock()
    mock_issue_response.status_code = 200
    mock_issue_response.text = '{"id": "16775066"}'
    mock_issue_response.json.return_value = {"id": "16775066"}

    # Second call: vote
    mock_vote_response = MagicMock()
    mock_vote_response.status_code = 200
    mock_vote_response.text = '{"status": "ok"}'
    mock_vote_response.json.return_value = {"status": "ok"}

    client.request.side_effect = [mock_issue_response, mock_vote_response]

    client.vote_story_points("ISSUE-123", 3)

    # Assert the request was made twice
    assert client.request.call_count == 2


def test_vote_story_points_failure(client, capsys):
    """
    This function tests the failure case of voting story points for an issue.

    Arguments:
    - client: An object representing the client used to interact with an API.
    - capsys: A fixture provided by pytest to capture stdout and stderr.

    Returns:
    This function does not return anything.

    Exceptions:
    This function does not raise any exceptions.
    """

    # First call: get issue ID
    mock_issue_response = MagicMock()
    mock_issue_response.status_code = 200
    mock_issue_response.text = '{"id": "16775066"}'
    mock_issue_response.json.return_value = {"id": "16775066"}

    # Second call: vote fails
    mock_vote_response = MagicMock()
    mock_vote_response.status_code = 400
    mock_vote_response.text = '{"error": "bad request"}'

    client.request.side_effect = [mock_issue_response, mock_vote_response]

    with pytest.raises(VoteStoryPointsError):
        client.vote_story_points("ISSUE-123", 3)

    captured = capsys.readouterr()
    assert "❌ Failed to vote on story points: JIRA API error (400):" in captured.out


def test_vote_story_points_fetch_issue_id_failure(client, capsys):
    """
    Simulate a failure scenario when fetching issue ID for voting on story points.

    Arguments:
    - client (object): An object representing the client used to make requests.
    - capsys (object): An object to capture stdout and stderr outputs.

    Exceptions:
    - FetchIssueIDError: Raised when there is a network error during the request.
    """

    # Simulate the first request (GET issue) raising an exception
    client.request.side_effect = FetchIssueIDError("network error")

    with pytest.raises(FetchIssueIDError):
        client.vote_story_points("ISSUE-123", 3)

    captured = capsys.readouterr()
    assert "❌ Failed to fetch issue ID for ISSUE-123: network error" in captured.out
