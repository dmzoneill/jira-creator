#!/usr/bin/env python
"""
Assigns an issue in Jira to a specific assignee.

Arguments:
- jira (JIRA): A JIRA client object used to interact with the Jira API.
- args (Namespace): An object containing parsed command-line arguments, including:
- issue_key (str): The key of the issue to be assigned.
- assignee (str): The username of the user to whom the issue will be assigned.

Return:
- bool: True if the issue was successfully assigned, False otherwise.

Side Effects:
- Prints a message indicating whether the issue assignment was successful or not.
"""

from argparse import Namespace

from rest.client import JiraClient


def cli_assign(jira: JiraClient, args: Namespace) -> bool:
    """
    Assigns an issue in Jira to a specific assignee.

    Arguments:
    - jira (JIRA): A JIRA client object used to interact with the Jira API.
    - args (Namespace): An object containing parsed command-line arguments, including:
    - issue_key (str): The key of the issue to be assigned.
    - assignee (str): The username of the user to whom the issue will be assigned.

    Return:
    - bool: True if the issue was successfully assigned, False otherwise.

    Side Effects:
    - Prints a message indicating whether the issue assignment was successful or not.
    """

    success: bool = jira.assign_issue(args.issue_key, args.assignee)
    print(
        f"✅ assigned {args.issue_key} to {args.assignee}"
        if success
        else f"❌ Could not assign {args.issue_key} to {args.assignee}"
    )
    return success
