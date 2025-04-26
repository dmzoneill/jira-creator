#!/usr/bin/env python
"""
This script defines a function cli_open_issue(args) that opens a JIRA issue in the default web browser using
subprocess.Popen. It retrieves the JIRA URL from the environment variables using the EnvFetcher class. If an
OpenIssueError is raised during the process, it prints an error message and raises the exception again.

Function cli_open_issue(args):
- Opens a JIRA issue in the default web browser using xdg-open.
- Arguments:
- _: JiraClient: Unused parameter (can be ignored).
- args (Namespace): A namespace containing the parsed arguments. It should have an attribute 'issue_key'
representing the key of the JIRA issue to open.
- Return:
- bool: True if the issue was successfully opened in the browser.
- Exceptions:
- OpenIssueError: Raised if there is an issue opening the JIRA issue in the browser.
- Side Effects:
- Opens the default web browser to display the JIRA issue specified by the 'issue_key'.
"""

# pylint: disable=consider-using-with

import subprocess
from argparse import Namespace

from core.env_fetcher import EnvFetcher
from exceptions.exceptions import OpenIssueError
from rest.client import JiraClient


def cli_open_issue(_: JiraClient, args: Namespace) -> bool:
    """
    Opens a JIRA issue in the default web browser using xdg-open.

    Arguments:
    - _: JiraClient: Unused parameter (can be ignored).
    - args (Namespace): A namespace containing the parsed arguments. It should have an attribute 'issue_key'
    representing the key of the JIRA issue to open.

    Return:
    - bool: True if the issue was successfully opened in the browser.

    Exceptions:
    - OpenIssueError: Raised if there is an issue opening the JIRA issue in the browser.

    Side Effects:
    - Opens the default web browser to display the JIRA issue specified by the 'issue_key'.
    """

    try:
        issue_url = f"{EnvFetcher.get('JIRA_URL')}/browse/{args.issue_key}"
        subprocess.Popen(["xdg-open", issue_url])
        return True
    except OpenIssueError as e:
        msg = f"❌ Failed to open issue {args.issue_key}: {e}"
        print(msg)
        raise OpenIssueError(e) from e
