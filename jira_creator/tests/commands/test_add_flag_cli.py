#!/usr/bin/env python
"""
This script contains a unit test function 'test_add_flag' that tests the 'add_flag' method of a CLI application.
It mocks the 'jira' method using MagicMock and asserts the expected behavior of the 'add_flag' method by checking the
output and method calls.
The test case validates that the 'add_flag' method returns a success status and calls the 'jira.add_flag' method with
the correct argument.

Functions:
- test_add_flag(cli, capsys): Simulates adding a flag to a Jira issue using a mock method. It takes 'cli' as an object
containing the Jira client and 'capsys' as a Pytest fixture capturing stdout and stderr output. It modifies the
'add_flag' method of the Jira client by replacing it with a MagicMock object.
"""

from unittest.mock import MagicMock


def test_add_flag(cli, capsys):
    """
    Simulates adding a flag to a Jira issue using a mock method.

    Arguments:
    - cli (object): An object containing the Jira client.
    - capsys (object): Pytest fixture capturing stdout and stderr output.

    Side Effects:
    - Modifies the 'add_flag' method of the Jira client by replacing it with a MagicMock object.
    """

    # Mock the jira method
    cli.jira.add_flag = MagicMock(return_value={"status": "success"})

    class Args:
        issue_key = "AAP-test_add_flag"

    response = cli.add_flag(Args())

    # Capture output and assert
    out, err = capsys.readouterr()
    assert "success" in response["status"]
    cli.jira.add_flag.assert_called_once_with("AAP-test_add_flag")
