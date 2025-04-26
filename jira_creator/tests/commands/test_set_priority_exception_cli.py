#!/usr/bin/env python
"""
This script contains a unit test function named test_set_priority_error, which tests the set_priority method of a CLI
class by mocking the set_priority method to raise a SetPriorityError exception. The test verifies that the exception is
raised correctly and that the expected error message is printed. The test uses pytest and unittest.mock modules for
testing and mocking functionalities.

test_set_priority_error:
Simulate an exception when setting priority in Jira for testing purposes.

Arguments:
- cli: An object representing the CLI (Command Line Interface) for Jira.
- capsys: A fixture provided by pytest for capturing stdout and stderr outputs during testing.

Exceptions:
- SetPriorityError: Raised when simulating a failure while setting priority in Jira.

Side Effects:
- Modifies the set_priority method of the Jira client to raise a SetPriorityError.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import SetPriorityError


def test_set_priority_error(cli, capsys):
    """
    Simulate an exception when setting priority in Jira for testing purposes.

    Arguments:
    - cli: An object representing the CLI (Command Line Interface) for Jira.
    - capsys: A fixture provided by pytest for capturing stdout and stderr outputs during testing.

    Exceptions:
    - SetPriorityError: Raised when simulating a failure while setting priority in Jira.

    Side Effects:
    - Modifies the set_priority method of the Jira client to raise a SetPriorityError.
    """

    # Mock the set_priority method to simulate an exception
    cli.jira.set_priority = MagicMock(side_effect=SetPriorityError("fail"))

    class Args:
        issue_key = "AAP-test_set_priority_error"
        priority = "High"

    with pytest.raises(SetPriorityError):
        # Call the method
        cli.set_priority(Args())

    # Capture the output
    out = capsys.readouterr().out

    # Assert that the correct error message was printed
    assert "❌ Failed to set priority" in out
