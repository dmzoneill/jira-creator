#!/usr/bin/env python
"""
This script contains a test function to simulate a failure scenario when fetching an issue description from Jira.

The test function takes a CLI object as an argument used to interact with Jira. It mocks the get_description method to
raise a FetchDescriptionError exception when fetching the issue description.

Test Function:
- test_edit_issue_fetch_fail(cli): Simulates a failure scenario when fetching an issue description.
Arguments:
- cli: A CLI object used to interact with Jira.
Exceptions:
- FetchDescriptionError: Raised when there is a failure in fetching the issue description.
"""
import pytest
from exceptions.exceptions import FetchDescriptionError


def test_edit_issue_fetch_fail(cli):
    """
    Simulates a failure scenario when fetching an issue description.

    Arguments:
    - cli: A CLI object used to interact with Jira.

    Exceptions:
    - FetchDescriptionError: Raised when there is a failure in fetching the issue description.
    """

    # Mocking the get_description method to raise an exception
    cli.jira.get_description.side_effect = FetchDescriptionError("fail")

    class Args:
        issue_key = "AAP-test_edit_issue_fetch_fail"
        no_ai = False

    with pytest.raises(FetchDescriptionError):
        cli.edit_issue(Args())
