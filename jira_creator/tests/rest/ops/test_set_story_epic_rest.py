from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_set_story_epic_rest(client):
    client._request = MagicMock(return_value={})

    # Call the function to set story points
    client.set_story_epic(
        "AAP-test_set_story_epic_rest", "AAP-test_set_story_epic_rest-1"
    )

    # Assert that the PUT request is called with the correct payload and endpoint
    client._request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/AAP-test_set_story_epic_rest",
        json={
            "fields": {
                EnvFetcher.get("JIRA_EPIC_FIELD"): "AAP-test_set_story_epic_rest-1"
            }
        },
    )
