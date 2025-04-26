#!/usr/bin/env python
"""
This module contains a function to remove a flag from a Jira issue using the provided Jira instance and command-line
arguments.

The 'cli_remove_flag' function takes two parameters:
- jira: An instance of the Jira API client.
- args: A dictionary containing the following key:
- issue_key (str): The key of the issue from which the flag will be removed.

It attempts to remove the flag from the specified issue using the 'jira.remove_flag' method. If successful, it prints a
success message indicating the flag removal. If an exception occurs during the removal process, it prints an error
message and raises a 'RemoveFlagError' with details of the failure.

Note: The 'RemoveFlagError' exception is imported from 'exceptions.exceptions' module.
"""

from argparse import Namespace
from typing import Any

from exceptions.exceptions import RemoveFlagError
from rest.client import JiraClient


def cli_remove_flag(jira: JiraClient, args: Namespace) -> Any:
    """
    Remove a flag from a Jira issue.

    Arguments:
    - jira: An instance of the Jira API client.
    - args: A dictionary containing the following key:
    - issue_key (str): The key of the issue from which the flag will be removed.

    Return:
    - The response from the Jira API after removing the flag.

    Exceptions:
    - RemoveFlagError: Raised if there is an issue while removing the flag from the Jira issue.

    Side Effects:
    - Prints a success message if the flag is removed successfully.
    - Prints an error message if there is a failure while removing the flag.
    """

    issue_key: str = args.issue_key
    try:
        response: Any = jira.remove_flag(issue_key)
        print(f"✅ Removed flag from issue '{issue_key}'")
        return response
    except RemoveFlagError as e:
        msg: str = f"❌ Failed to remove flag from issue '{issue_key}': {e}"
        print(msg)
        raise RemoveFlagError(e) from e
