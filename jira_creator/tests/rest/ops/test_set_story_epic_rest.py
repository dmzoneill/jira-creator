#!/usr/bin/env python
"""
This file contains a test function to set story epic in a client using a mocked request. The function calls the
'set_story_epic' method on the client object with specific parameters and then asserts that a PUT request is made with
the correct payload and endpoint using a mocked '_request' method.

The 'test_set_story_epic_rest' function is used to test the setting of the story epic REST endpoint. It takes a 'client'
parameter, which is an instance of a client class used to make REST API requests. Within the function, the '_request'
attribute of the client is modified by replacing it with a MagicMock object. The function then sets the story epic using
specific parameters and asserts that a PUT request is made with the correct payload and endpoint.

Side Effects:
- Modifies the _request attribute of the client by replacing it with a MagicMock object.
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

    client.request = MagicMock(return_value={})

    # Call the function to set story points
    client.set_story_epic(
        "AAP-test_set_story_epic_rest", "AAP-test_set_story_epic_rest-1"
    )

    # Assert that the PUT request is called with the correct payload and endpoint
    client.request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/AAP-test_set_story_epic_rest",
        json_data={
            "fields": {
                EnvFetcher.get("JIRA_EPIC_FIELD"): "AAP-test_set_story_epic_rest-1"
            }
        },
    )
