#!/usr/bin/env python
"""
This script defines a function cli_change_type that changes the issue type of a Jira issue. It takes two arguments:
'jira' representing the Jira instance and 'args' containing the issue key and the new issue type.
If the issue type change is successful, it prints a success message; otherwise, it prints a failure message.
If an exception of type ChangeTypeError is caught during the process, it prints an error message, raises the same
exception, and propagates it.

Function cli_change_type:
- Change the type of a Jira issue.
- Arguments:
- jira (JIRA): A JIRA instance to interact with the Jira service.
- args (Namespace): An object containing the following attributes:
- issue_key (str): The key of the issue to be changed.
- new_type (str): The new type to assign to the issue.
- Return:
- bool: True if the issue type change was successful, False otherwise.
- Exceptions:
- ChangeTypeError: Raised when an error occurs during the issue type change process.
- Side Effects:
- Prints a success or failure message indicating the result of the issue type change.
"""

from argparse import Namespace

from exceptions.exceptions import ChangeTypeError
from rest.client import JiraClient  # Assuming JIRA is imported from a library


def cli_change_type(jira: JiraClient, args: Namespace) -> bool:
    """
    Change the type of a Jira issue.

    Arguments:
    - jira (JIRA): A JIRA instance to interact with the Jira service.
    - args (Namespace): An object containing the following attributes:
    - issue_key (str): The key of the issue to be changed.
    - new_type (str): The new type to assign to the issue.

    Return:
    - bool: True if the issue type change was successful, False otherwise.

    Exceptions:
    - ChangeTypeError: Raised when an error occurs during the issue type change process.

    Side Effects:
    - Prints a success or failure message indicating the result of the issue type change.
    """

    try:
        if jira.change_issue_type(args.issue_key, args.new_type):
            print(f"✅ Changed {args.issue_key} to '{args.new_type}'")
            return True
        print(f"❌ Change failed for {args.issue_key}")
        return False
    except ChangeTypeError as e:
        msg = f"❌ Error: {e}"
        print(msg)
        raise ChangeTypeError(e) from e
