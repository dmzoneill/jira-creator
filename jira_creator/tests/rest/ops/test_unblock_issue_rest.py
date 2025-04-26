#!/usr/bin/env python
"""
This script defines a test function to verify that the 'unblock_issue' method in a client class is calling the expected
fields with the correct values. It sets up a fake request function to capture the method, path, and json data sent by
the client during the test. The test asserts that the method is 'PUT', the path matches the expected JIRA API endpoint,
and the json data includes specific fields with predefined values.

The 'test_unblock_issue_calls_expected_fields' function is used to test if a specific client function correctly calls
expected fields. It takes a 'client' object as an argument and modifies the 'called' dictionary to keep track of called
fields.

The 'fake_request' function is used to make a fake HTTP request with the specified method, path, and optional JSON
data. It returns an empty dictionary representing the response from the fake request.
"""

from core.env_fetcher import EnvFetcher


def test_unblock_issue_calls_expected_fields(client):
    """
    Summary:
    This function is used to test if a specific client function correctly calls expected fields.

    Arguments:
    - client (object): The client object being tested.

    Side Effects:
    - Modifies the 'called' dictionary to keep track of called fields.
    """

    called = {}

    def fake_request(method, path, json_data=None, **kwargs):
        """
        Make a fake HTTP request with the specified method and path.

        Arguments:
        - method (str): The HTTP method to use for the request (e.g., 'GET', 'POST').
        - path (str): The path or endpoint to send the request to.
        - json_data (dict): Optional. A dictionary containing the JSON data to be sent in the request body.
        - **kwargs: Additional keyword arguments that are not used in this function.

        Return:
        - dict: An empty dictionary representing the response from the fake request.
        """

        called["method"] = method
        called["path"] = path
        called["json_data"] = json_data
        return {}

    client.request = fake_request

    client.unblock_issue("AAP-test_unblock_issue_calls_expected_fields")

    assert called["method"] == "PUT"
    assert (
        called["path"]
        == "/rest/api/2/issue/AAP-test_unblock_issue_calls_expected_fields"
    )
    assert called["json_data"] == {
        "fields": {
            EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": False},
            EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "",
        }
    }
