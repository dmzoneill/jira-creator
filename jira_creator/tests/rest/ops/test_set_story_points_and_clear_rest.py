from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_set_story_points(client):
    client._request = MagicMock(return_value={})

    # Call the function to set story points
    client.set_story_points("AAP-test_set_story_points", 8)

    # Assert that the PUT request is called with the correct payload and endpoint
    client._request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/AAP-test_set_story_points",
        json={"fields": {EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 8}},
    )
