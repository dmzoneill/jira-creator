#!/usr/bin/env python
"""
Unassign an issue in Jira.

Arguments:
- jira: An instance of the Jira API client.
- args: A namespace containing the issue key to unassign.

Return:
- bool: True if the issue was successfully unassigned, False otherwise.
"""


def cli_unassign(jira, args):
    """
    Unassign an issue in Jira.

    Arguments:
    - jira: An instance of the Jira API client.
    - args: A namespace containing the issue key to unassign.

    Return:
    - bool: True if the issue was successfully unassigned, False otherwise.
    """

    success = jira.unassign_issue(args.issue_key)
    print(
        f"✅ Unassigned {args.issue_key}"
        if success
        else f"❌ Could not unassign {args.issue_key}"
    )
    return bool(success)
