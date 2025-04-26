#!/usr/bin/env python
"""
Unassign an issue in Jira.

This script contains a function 'cli_unassign' that unassigns an issue in Jira. The function takes two arguments:
- jira: An instance of the Jira API client.
- args: A namespace containing the issue key to unassign.

It returns a boolean value:
- True if the issue was successfully unassigned.
- False otherwise.
"""

from argparse import Namespace

from rest.client import JiraClient


def cli_unassign(jira: JiraClient, args: Namespace) -> bool:
    """
    Unassign an issue in Jira.

    Arguments:
    - jira: An instance of the Jira API client.
    - args: A namespace containing the issue key to unassign.

    Return:
    - bool: True if the issue was successfully unassigned, False otherwise.
    """

    success: bool = jira.unassign_issue(args.issue_key)
    print(
        f"✅ Unassigned {args.issue_key}"
        if success
        else f"❌ Could not unassign {args.issue_key}"
    )
    return success
