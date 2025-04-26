#!/usr/bin/env python
"""
Set the status of a JIRA issue using the provided JIRA client and arguments.

Arguments:
- jira (JIRA): A JIRA client object used to interact with the JIRA API.
- args (Namespace): A namespace object containing the following attributes:
- issue_key (str): The key of the JIRA issue to update.
- status (str): The new status to set for the JIRA issue.

Return:
- bool: True if the status is successfully set.

Exceptions:
- SetStatusError: Raised when there is an error setting the status of the JIRA issue.

Side Effects:
- Prints a success message if the status is set successfully.
- Prints an error message and raises a SetStatusError if there is a failure.
"""
from argparse import Namespace

from exceptions.exceptions import SetStatusError
from rest.client import JiraClient


def cli_set_status(jira: JiraClient, args: Namespace) -> bool:
    """
    Set the status of a JIRA issue using the provided JIRA client and arguments.

    Arguments:
    - jira (JIRA): A JIRA client object used to interact with the JIRA API.
    - args (Namespace): A namespace object containing the following attributes:
    - issue_key (str): The key of the JIRA issue to update.
    - status (str): The new status to set for the JIRA issue.

    Return:
    - bool: True if the status is successfully set.

    Exceptions:
    - SetStatusError: Raised when there is an error setting the status of the JIRA issue.

    Side Effects:
    - Prints a success message if the status is set successfully.
    - Prints an error message and raises a SetStatusError if there is a failure.
    """

    try:
        jira.set_status(args.issue_key, args.status)
        print(f"✅ Status set to '{args.status}'")
        return True
    except SetStatusError as e:
        msg = f"❌ Failed to update status: {e}"
        print(msg)
        raise SetStatusError(e) from e
