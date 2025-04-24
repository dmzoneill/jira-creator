#!/usr/bin/env python
"""
This script defines a test function test_migrate_to_exception that tests the migration functionality of a CLI
application. The test mocks the necessary objects and asserts that the migration process raises a MigrateError
exception with a specific error message. The test also captures the output and verifies the error message. The script
uses pytest for testing and unittest.mock for mocking objects.

Functions:
- test_migrate_to_exception: Mocks the migrate_issue method to raise an exception and tests the migration process. It
takes
cli (Command Line Interface object) and capsys (pytest fixture to capture stdout and stderr) as arguments. It raises
MigrateError when the migrate_issue method fails and modifies the migrate_issue method to raise an exception. It also
sets
the jira_url attribute of cli to "http://fake".
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import MigrateError


def test_migrate_to_exception(cli, capsys):
    """
    Mock the migrate_issue method to raise an exception and test the migration process.

    Arguments:
    - cli: Command Line Interface object.
    - capsys: pytest fixture to capture stdout and stderr.

    Exceptions:
    - MigrateError: Raised when the migrate_issue method fails.

    Side Effects:
    - Modifies the migrate_issue method to raise an exception.
    - Sets the jira_url attribute of cli to "http://fake".
    """

    # Mock the migrate_issue method to raise an exception
    cli.jira.migrate_issue = MagicMock(side_effect=MigrateError("fail"))
    cli.jira.jira_url = "http://fake"

    # Mock the Args class with necessary attributes
    class Args:
        issue_key = "AAP-test_migrate_to_exception"
        new_type = "story"

    with pytest.raises(MigrateError):
        # Call the migrate method
        cli.migrate(Args())

    # Capture the output and assert the error message
    out = capsys.readouterr().out
    assert "❌ Migration failed" in out
