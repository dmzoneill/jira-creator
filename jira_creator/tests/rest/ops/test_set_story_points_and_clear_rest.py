"""
This script contains a test function to validate the functionality of setting story points in a JIRA issue using a
client object. The test function mocks the client's _request method and asserts that a PUT request is made with the
correct payload and endpoint. The EnvFetcher class is used to retrieve the JIRA story points field value.
"""

from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_set_story_points(client):
    """
    Set story points for a given client.

    Arguments:
    - client (object): The client object for which story points need to be set.

    Side Effects:
    - Modifies the client's request attribute using MagicMock to return an empty dictionary.
    """

    client._request = MagicMock(return_value={})

    # Call the function to set story points
    client.set_story_points("AAP-test_set_story_points", 8)

    # Assert that the PUT request is called with the correct payload and endpoint
    client._request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/AAP-test_set_story_points",
        json={"fields": {EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 8}},
    )
