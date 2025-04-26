#!/usr/bin/env python
"""
Clones a Jira issue by adding a flag to it.

Arguments:
- jira (Jira): An instance of the Jira API client.
- args (CloneIssueArgs): An object containing the following attribute:
- issue_key (str): The key of the issue to be cloned.

Return:
- dict: The response from adding a flag to the specified Jira issue.
"""

from argparse import Namespace
from typing import Any, Dict

from rest.client import JiraClient


def cli_clone_issue(jira: JiraClient, args: Namespace) -> Dict[str, Any]:
    """
    Clones a Jira issue by adding a flag to it.

    Arguments:
    - jira (Jira): An instance of the Jira API client.
    - args (CloneIssueArgs): An object containing the following attribute:
    - issue_key (str): The key of the issue to be cloned.

    Return:
    - dict: The response from adding a flag to the specified Jira issue.
    """

    issue_key: str = args.issue_key
    response: Dict[str, Any] = jira.clone_issue(issue_key)
    return response
