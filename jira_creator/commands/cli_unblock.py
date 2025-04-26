#!/usr/bin/env python
"""
Unblocks a Jira issue.

This script provides a function 'cli_unblock' that unblocks a Jira issue. It takes two arguments:
- jira (JIRA): A JIRA instance used to interact with the Jira API.
- args (Namespace): A namespace object containing parsed command-line arguments. It should have an 'issue_key'
attribute representing the key of the issue to be unblocked.

Returns a boolean value:
- True if the issue was successfully unblocked.

Raises an UnBlockError exception if there was an error while trying to unblock the issue.

Side Effects:
- Prints a success message if the issue is unblocked successfully.
- Prints an error message if there is a failure while unblocking the issue.
"""
from argparse import Namespace

from exceptions.exceptions import UnBlockError
from rest.client import JiraClient


def cli_unblock(jira: JiraClient, args: Namespace) -> bool:
    """
    Unblocks a Jira issue.

    Arguments:
    - jira (JIRA): A JIRA instance used to interact with the Jira API.
    - args (Namespace): A namespace object containing parsed command-line arguments. It should have an 'issue_key'
    attribute representing the key of the issue to be unblocked.

    Return:
    - bool: True if the issue was successfully unblocked.

    Exceptions:
    - UnBlockError: Raised if there was an error while trying to unblock the issue.

    Side Effects:
    - Prints a success message if the issue is unblocked successfully.
    - Prints an error message if there is a failure while unblocking the issue.
    """

    try:
        jira.unblock_issue(args.issue_key)
        print(f"✅ {args.issue_key} marked as unblocked")
        return True
    except UnBlockError as e:
        msg = f"❌ Failed to unblock {args.issue_key}: {e}"
        print(msg)
        raise UnBlockError(e) from e
