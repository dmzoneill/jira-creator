#!/usr/bin/env python
"""
Adds a flag to a Jira issue specified by the given issue key.

Args:
jira (JIRA): An instance of the Jira client used to interact with the Jira API.
args (Namespace): A namespace object containing the command-line arguments passed to the script.
It should contain the 'issue_key' attribute which represents the key of the Jira issue to add the flag to.

Returns:
Dict: A dictionary representing the response received after adding the flag to the Jira issue.
"""
from argparse import Namespace
from typing import Dict

from rest.client import JiraClient


def cli_add_flag(jira: JiraClient, args: Namespace) -> Dict:
    """
    Adds a flag to a Jira issue specified by the given issue key.

    Args:
    jira (JIRA): An instance of the Jira client used to interact with the Jira API.
    args (Namespace): A namespace object containing the command-line arguments passed to the script.
    It should contain the 'issue_key' attribute which represents the key of the Jira issue to add the flag to.

    Returns:
    Dict: A dictionary representing the response received after adding the flag to the Jira issue.
    """

    issue_key: str = args.issue_key
    response: Dict = jira.add_flag(issue_key)
    return response
