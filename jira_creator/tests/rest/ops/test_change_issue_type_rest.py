#!/usr/bin/env python
"""
This module contains unit tests for methods related to changing issue types in a Jira client.

The tests include:
- `test_change_issue_type`: Verifies the functionality of the `change_issue_type` method by mocking the request method
and ensuring that the correct GET and PUT requests are made to retrieve and change the issue type.
- `test_change_type_else_block`: Tests the `change_type` method by simulating a failure scenario where the
`change_issue_type` method returns False, and asserts that the appropriate failure message is printed.

Dependencies:
- unittest.mock: Used for mocking objects and methods during testing.
"""

from unittest.mock import MagicMock, patch


def test_change_issue_type(client):
    """
    Mock the request method to fetch issue details and change the issue type if needed.

    Arguments:
    - client: A client object used to interact with an external service.

    Side Effects:
    - Modifies the behavior of the request method to return issue details with a specific issue type based on the
    method and path provided.
    """

    # Mock the request method
    mock_request = MagicMock()
    # First call: GET request to fetch issue details
    mock_request.side_effect = lambda method, path, **kwargs: (
        {"fields": {"issuetype": {"subtask": True}}} if method == "GET" else {}
    )

    # Assign the mocked _request method to the client
    client.request = mock_request

    # Call the method
    client.change_issue_type("AAP-test_change_issue_type", "story")

    # Assert that the GET request was called to retrieve the issue
    mock_request.assert_any_call("GET", "/rest/api/2/issue/AAP-test_change_issue_type")

    # Assert that the PUT request was called to change the issue type
    mock_request.assert_any_call(
        "PUT",
        "/rest/api/2/issue/AAP-test_change_issue_type",
        json_data={
            "fields": {"issuetype": {"name": "Story"}},
            "update": {"parent": [{"remove": {}}]},
        },
    )


def test_change_type_else_block(cli):
    """
    Change the type of an issue in a CLI application if the condition in the else block is met.

    Arguments:
    - cli: The CLI object used for interacting with the command line interface.

    Side Effects:
    - Modifies the type of an issue specified by 'issue_key' to the type specified by 'new_type'.
    """

    # Mocking Args for issue_key and new_type
    class Args:
        issue_key = "AAP-test_change_type_else_block"
        new_type = "bug"

    # Mock the JiraClient's change_issue_type to return False to hit the else block
    with patch.object(cli.jira, "change_issue_type", return_value=False):
        # Mocking the print function to capture the output
        with patch("builtins.print") as mock_print:
            # Call the change_type method
            cli.change_type(Args())

            # Ensure that print was called with the correct "❌ Change failed" message
            mock_print.assert_called_with(
                "❌ Change failed for AAP-test_change_type_else_block"
            )
