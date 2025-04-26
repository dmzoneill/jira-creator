#!/usr/bin/env python
"""
Marks a Jira issue as blocked.

Arguments:
- jira (JIRA): An instance of the JIRA API client.
- args (Namespace): A namespace containing the following attributes:
- issue_key (str): The key of the issue to be blocked.
- reason (str): The reason for blocking the issue.

Return:
- bool: True if the issue was successfully marked as blocked.

Exceptions:
- BlockError: Raised if there is an error while trying to mark the issue as blocked.
"""
from argparse import Namespace

from exceptions.exceptions import BlockError
from rest.client import JiraClient


def cli_block(jira: JiraClient, args: Namespace) -> bool:
    """
    Marks a Jira issue as blocked.

    Arguments:
    - jira (JIRA): An instance of the JIRA API client.
    - args (Namespace): A namespace containing the following attributes:
    - issue_key (str): The key of the issue to be blocked.
    - reason (str): The reason for blocking the issue.

    Return:
    - bool: True if the issue was successfully marked as blocked.

    Exceptions:
    - BlockError: Raised if there is an error while trying to mark the issue as blocked.
    """

    try:
        jira.block_issue(args.issue_key, args.reason)
        print(f"✅ {args.issue_key} marked as blocked: {args.reason}")
        return True
    except BlockError as e:
        msg = f"❌ Failed to mark {args.issue_key} as blocked: {e}"
        print(msg)
        raise BlockError(e) from e
