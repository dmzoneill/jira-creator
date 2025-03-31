from unittest.mock import MagicMock, patch

import pytest
from jira.client import JiraClient


@pytest.fixture
def client():
    return JiraClient()


@patch("jira.client.requests.request")
def test_vote_story_points_success(mock_request, client):
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

    mock_request.side_effect = [mock_issue_response, mock_vote_response]

    client.vote_story_points("ISSUE-123", 3)

    # Assert the request was made twice
    assert mock_request.call_count == 2


@patch("jira.client.requests.request")
def test_vote_story_points_failure(mock_request, client, capsys):
    # First call: get issue ID
    mock_issue_response = MagicMock()
    mock_issue_response.status_code = 200
    mock_issue_response.text = '{"id": "16775066"}'
    mock_issue_response.json.return_value = {"id": "16775066"}

    # Second call: vote fails
    mock_vote_response = MagicMock()
    mock_vote_response.status_code = 400
    mock_vote_response.text = '{"error": "bad request"}'

    mock_request.side_effect = [mock_issue_response, mock_vote_response]

    client.vote_story_points("ISSUE-123", 3)

    captured = capsys.readouterr()
    assert "❌ Failed to vote on story points: JIRA API error (400):" in captured.out


@patch("jira.client.requests.request")
def test_vote_story_points_fetch_issue_id_failure(mock_request, client, capsys):
    # Simulate the first request (GET issue) raising an exception
    mock_request.side_effect = Exception("network error")

    client.vote_story_points("ISSUE-123", 3)

    captured = capsys.readouterr()
    assert "❌ Failed to fetch issue ID for ISSUE-123: network error" in captured.out
