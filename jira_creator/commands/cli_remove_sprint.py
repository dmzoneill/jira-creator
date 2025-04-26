#!/usr/bin/env python
"""
Remove an issue from a sprint in Jira.

Arguments:
- jira (JIRA): An instance of the JIRA API client.
- args (Namespace): A namespace containing the issue key to be removed from the sprint.

Return:
- bool: True if the issue was successfully removed from the sprint.

Exceptions:
- RemoveFromSprintError: Raised if there is an error while removing the issue from the sprint.

Side Effects:
- Prints a success message if the issue is removed from the sprint.
- Prints an error message and raises a RemoveFromSprintError if removal fails.
"""
from argparse import Namespace

from exceptions.exceptions import RemoveFromSprintError
from rest.client import JiraClient


def cli_remove_sprint(jira: JiraClient, args: Namespace) -> bool:
    """
    Remove an issue from a sprint in Jira.

    Arguments:
    - jira (JIRA): An instance of the JIRA API client.
    - args (Namespace): A namespace containing the issue key to be removed from the sprint.

    Return:
    - bool: True if the issue was successfully removed from the sprint.

    Exceptions:
    - RemoveFromSprintError: Raised if there is an error while removing the issue from the sprint.

    Side Effects:
    - Prints a success message if the issue is removed from the sprint.
    - Prints an error message and raises a RemoveFromSprintError if removal fails.
    """

    try:
        jira.remove_from_sprint(args.issue_key)
        print("✅ Removed from sprint")
        return True
    except RemoveFromSprintError as e:
        msg = f"❌ Failed to remove sprint: {e}"
        print(msg)
        raise RemoveFromSprintError(e) from e
