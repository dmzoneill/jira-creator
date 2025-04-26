#!/usr/bin/env python
"""
Sets a flag to a specified Jira issue.

This script provides a function 'cli_set_summary' that sets a flag to a specified Jira issue using a JiraClient
instance and arguments provided. The function takes 'jira' as a JiraClient instance and 'args' as a Namespace object
containing the issue key. It then returns a response from the Jira API after adding the flag to the specified issue.

Dependencies:
- JiraClient: A custom class for interacting with the Jira API.
- Namespace: A class from the argparse module used to hold command-line arguments.

Functions:
- cli_set_summary(jira: JiraClient, args: Namespace) -> Dict[str, Any]: Sets a flag to a specified Jira issue and
returns a response from the Jira API after adding the flag.

Returns:
- Dict[str, Any]: A response from the Jira API after adding the flag to the specified issue.
"""
from argparse import Namespace
from typing import Any, Dict

from rest.client import JiraClient


def cli_set_summary(jira: JiraClient, args: Namespace) -> Dict[str, Any]:
    """
    Sets a flag to a specified Jira issue.

    Arguments:
    - jira (JIRA): An instance of the Jira client used to interact with the Jira API.
    - args (Dict[str, Any]): A dictionary containing the arguments passed to the function. It should contain the issue
    key.

    Return:
    - Dict[str, Any]: A response from the Jira API after adding the flag to the specified issue.
    """

    issue_key: str = args.issue_key
    response: Dict[str, Any] = jira.add_flag_to_issue(issue_key)
    return response
