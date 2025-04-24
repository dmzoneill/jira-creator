#!/usr/bin/env python
"""
This file contains test cases for the 'remove_flag' method in the 'cli' module.
It includes tests to check the successful removal of a flag and also to handle exceptions.
The tests utilize the 'MagicMock' class from the 'unittest.mock' module and 'pytest' for assertions.
The 'test_remove_flag' function mocks the 'remove_flag' method and asserts the output and response.
The 'test_remove_flag_exception' function mocks the 'remove_flag' method to raise an exception and verifies the
exception handling.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import RemoveFlagError


def test_remove_flag(cli, capsys):
    """
    Simulate the removal of a flag from a Jira instance using a mock method.

    Arguments:
    - cli: An object representing the Jira client.
    - capsys: A fixture provided by pytest to capture stdout and stderr outputs.

    Side Effects:
    - Sets up a mock method for the remove_flag function in the Jira client object.
    """

    # Mock the remove_flag method
    cli.jira.remove_flag = MagicMock(return_value={"status": "success"})

    class Args:
        issue_key = "AAP-test_remove_flag"

    response = cli.remove_flag(Args())

    # Capture output and assert
    out = capsys.readouterr().out
    assert "Removed" in out
    assert response == {"status": "success"}


def test_remove_flag_exception(cli, capsys):
    """
    Mocks the 'remove_flag' method of a Jira client and sets it to raise an exception when called.

    Arguments:
    - cli: Jira client object.
    - capsys: Pytest fixture for capturing stdout and stderr.

    Exceptions:
    - Exception: Raised with message "Failed" when the 'remove_flag' method is called.
    """

    # Mock the list_sprints method
    cli.jira.remove_flag = MagicMock(side_effect=RemoveFlagError("Failed"))

    class Args:
        issue_key = "dummy_issue_key"

    with pytest.raises(RemoveFlagError):
        cli.remove_flag(Args())
