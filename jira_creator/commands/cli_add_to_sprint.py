#!/usr/bin/env python
"""
Adds an issue to a sprint in Jira.

This script provides a function 'cli_add_to_sprint' that adds an issue to a sprint in Jira. It takes two arguments:
- jira (JIRA): An instance of the JIRA client.
- args (Namespace): A namespace object containing 'issue_key' and 'sprint_name' attributes.

The function returns a boolean value:
- True if the issue was successfully added to the sprint.

It may raise an 'AddSprintError' exception if an error occurs during the process.

Side effects include:
- Printing a success message if the issue is added to the sprint.
- Printing an error message and raising 'AddSprintError' if an error occurs during the process.
"""
from argparse import Namespace

from exceptions.exceptions import AddSprintError
from rest.client import JiraClient


def cli_add_to_sprint(jira: JiraClient, args: Namespace) -> bool:
    """
    Adds an issue to a sprint in Jira.

    Arguments:
    - jira (JIRA): An instance of the JIRA client.
    - args (Namespace): A namespace object containing 'issue_key', 'sprint_name' and 'assignee' attributes.

    Return:
    - bool: True if the issue was successfully added to the sprint.

    Exceptions:
    - AddSprintError: Raised when an error occurs while adding the issue to the sprint.

    Side Effects:
    - Prints a success message if the issue is added to the sprint.
    - Prints an error message and raises AddSprintError if an error occurs during the process.
    """

    try:
        jira.add_to_sprint(args.issue_key, args.sprint_name, args.assignee)
        print(f"✅ Added to sprint '{args.sprint_name}'")
        return True
    except AddSprintError as e:
        msg = f"❌ {e}"
        print(msg)
        raise AddSprintError(e) from e
