#!/usr/bin/env python
"""
This script contains a unit test for the 'migrate' method in a CLI application. It mocks the 'migrate_issue' method and
'jira_url' attribute of a 'cli' object using MagicMock. It also creates a mock 'Args' class with 'issue_key' and
'new_type' attributes. The 'migrate' method is then called with an instance of the 'Args' class for testing purposes.

Functions:
- test_migrate_success_print(cli): Mocks the migrate_issue method and sets the jira_url for the CLI.

Arguments:
- cli: An instance of the CLI class.

Side Effects:
- Sets the return value of the migrate_issue method to "AAP-test_migrate_success_print-0".
- Sets the jira_url attribute of the cli.jira instance to "http://fake".
"""

from unittest.mock import MagicMock


def test_migrate_success_print(cli):
    """
    Mock the migrate_issue method and set the Jira URL for the CLI.

    Arguments:
    - cli: An instance of the CLI class.

    Side Effects:
    - Sets the return value of the migrate_issue method to "AAP-test_migrate_success_print-0".
    - Sets the jira_url attribute of the cli.jira instance to "http://fake".
    """

    # Mock the migrate_issue method
    cli.jira.migrate_issue = MagicMock(return_value="AAP-test_migrate_success_print-0")
    cli.jira.jira_url = "http://fake"

    # Mock the Args class with necessary attributes
    class Args:
        issue_key = "AAP-test_migrate_success_print-1"
        new_type = "story"

    # Call the migrate method
    cli.migrate(Args())
