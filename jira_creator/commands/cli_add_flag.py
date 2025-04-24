#!/usr/bin/env python
"""
Adds a flag to a Jira issue specified by the given issue key.

Args:
jira (Jira): An instance of the Jira client used to interact with the Jira API.
args (Namespace): A namespace object containing the command-line arguments passed to the script.
It should contain the 'issue_key' attribute which represents the key of the Jira issue to add the flag to.

Returns:
dict: A dictionary representing the response received after adding the flag to the Jira issue.
"""


def cli_add_flag(jira, args):
    """
    Adds a flag to a Jira issue specified by the given issue key.

    Args:
    jira (Jira): An instance of the Jira client used to interact with the Jira API.
    args (Namespace): A namespace object containing the command-line arguments passed to the script.
    It should contain the 'issue_key' attribute which represents the key of the Jira issue to add the flag to.

    Returns:
    dict: A dictionary representing the response received after adding the flag to the Jira issue.
    """

    issue_key = args.issue_key
    response = jira.add_flag(issue_key)
    return response
