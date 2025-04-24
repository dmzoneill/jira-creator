#!/usr/bin/env python
"""
View a specific issue using the client.

Arguments:
- client (Client): An instance of the client used to interact with the issue tracking system.

This function calls the 'view_issue' method of the client to view a specific issue with the key
"AAP-test_rest_view_issue".
"""


def test_rest_view_issue(client):
    """
    View a specific issue using the client.

    Arguments:
    - client (Client): An instance of the client used to interact with the issue tracking system.

    This function calls the 'view_issue' method of the client to view a specific issue with the key
    "AAP-test_rest_view_issue".
    """

    # Call the method to set priority
    client.view_issue("AAP-test_rest_view_issue")

    # Update the test to expect the 'allow_204' argument
    client.request.assert_called_once_with(
        "GET",
        "/rest/api/2/issue/AAP-test_rest_view_issue",
    )
