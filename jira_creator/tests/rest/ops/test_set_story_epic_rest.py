"""
This file contains a test function to set story epic in a client using a mocked request. The function calls the
'set_story_epic' method on the client object with specific parameters and then asserts that a PUT request is made with
the correct payload and endpoint using a mocked '_request' method.
"""

from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_set_story_epic_rest(client):
    """
    Set the story epic REST endpoint test.

    Arguments:
    - client: An instance of a client class used to make REST API requests.

    Side Effects:
    - Modifies the _request attribute of the client by replacing it with a MagicMock object.

    """

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
