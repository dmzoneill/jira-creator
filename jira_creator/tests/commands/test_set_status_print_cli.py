#!/usr/bin/env python
"""
This script contains a test case for the set_status method in a CLI application.
It mocks the set_status method using MagicMock and then calls the set_status method with specific arguments.
Finally, it asserts that the set_status method was called with the correct arguments.

Functions:
- test_set_status_print(cli): Mocks the set_status method for a given CLI object and asserts the correct arguments
passed to set_status.

Side Effects:
- Modifies the set_status method of the jira attribute in the provided CLI object.
"""

from unittest.mock import MagicMock


def test_set_status_print(cli):
    """
    Mock the set_status method for a given CLI object.

    Arguments:
    - cli (object): The CLI object for which the set_status method is being mocked.

    Side Effects:
    - Modifies the set_status method of the jira attribute in the provided CLI object.
    """

    # Mock the set_status method
    cli.jira.set_status = MagicMock()

    class Args:
        issue_key = "AAP-test_set_status_print"
        status = "Done"

    # Call the method
    cli.set_status(Args())

    # Assert that set_status was called with the correct arguments
    cli.jira.set_status.assert_called_once_with("AAP-test_set_status_print", "Done")
