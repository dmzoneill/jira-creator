from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import FetchIssueIDError, VoteStoryPointsError


def test_vote_story_points_success(client):
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

    client._request.side_effect = [mock_issue_response, mock_vote_response]

    client.vote_story_points("ISSUE-123", 3)

    # Assert the request was made twice
    assert client._request.call_count == 2


def test_vote_story_points_failure(client, capsys):
    # First call: get issue ID
    mock_issue_response = MagicMock()
    mock_issue_response.status_code = 200
    mock_issue_response.text = '{"id": "16775066"}'
    mock_issue_response.json.return_value = {"id": "16775066"}

    # Second call: vote fails
    mock_vote_response = MagicMock()
    mock_vote_response.status_code = 400
    mock_vote_response.text = '{"error": "bad request"}'

    client._request.side_effect = [mock_issue_response, mock_vote_response]

    with pytest.raises(VoteStoryPointsError):
        client.vote_story_points("ISSUE-123", 3)

    captured = capsys.readouterr()
    assert "❌ Failed to vote on story points: JIRA API error (400):" in captured.out


def test_vote_story_points_fetch_issue_id_failure(client, capsys):
    # Simulate the first request (GET issue) raising an exception
    client._request.side_effect = FetchIssueIDError("network error")

    with pytest.raises(FetchIssueIDError):
        client.vote_story_points("ISSUE-123", 3)

    captured = capsys.readouterr()
    assert "❌ Failed to fetch issue ID for ISSUE-123: network error" in captured.out
