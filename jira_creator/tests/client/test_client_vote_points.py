from unittest.mock import MagicMock

from jira.client import JiraClient


def test_vote_story_points():
    client = JiraClient()
    client._request = MagicMock(return_value={"status": "ok"})

    client.vote_story_points("AAP-100", 3)
