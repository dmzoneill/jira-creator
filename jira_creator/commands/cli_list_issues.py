#!/usr/bin/env python
"""
This module provides a command-line interface (CLI) for listing issues from a Jira project using the JiraClient.

The `cli_list_issues` function retrieves and formats issues based on various filters such as project, component,
reporter, and assignee. It allows users to dynamically select columns and sort the output for better readability.

Key functionalities:
- Fetch issues from Jira according to specified criteria.
- Flatten issue fields for easier processing.
- Generate headers based on user-defined or default view columns.
- Filter and sort issues based on user input.
- Handle errors related to issue listing gracefully.

Dependencies:
- `core.columns`: Utility functions for manipulating issue data.
- `core.env_fetcher`: Fetches environment-specific configurations.
- `exceptions.exceptions`: Custom exception handling for listing errors.
- `rest.client`: Contains the JiraClient for Jira API interactions.
"""

# pylint: disable=too-many-statements too-many-branches

import traceback
from argparse import Namespace
from typing import Any, List

from core.view_helpers import format_and_print_rows, massage_issue_list
from exceptions.exceptions import ListIssuesError
from rest.client import JiraClient


def cli_list_issues(jira: JiraClient, args: Namespace) -> List[Any]:
    """
    Lists issues from a JIRA project based on specified criteria and formats the output for display.

    Args:
    jira (JiraClient): An instance of the JiraClient used to interact with the JIRA API.
    args (Namespace): Command-line arguments containing filters for the issues, including:
    - project (str): The project key to filter issues by.
    - component (str): The component to filter issues by.
    - reporter (str, optional): The reporter to filter issues by.
    - assignee (str, optional): The assignee to filter issues by (used only if reporter is not specified).
    - status (str, optional): The status to filter issues by.
    - summary (str, optional): A substring to search for in the issue summary.
    - blocked (bool, optional): If true, only include blocked issues.
    - unblocked (bool, optional): If true, only include unblocked issues.
    - sort (str, optional): Columns to sort the output by.

    Returns:
    List[Any]: A list of issues retrieved from JIRA, which may include flattened fields.

    Raises:
    ListIssuesError: If there is an error while attempting to list issues from JIRA.
    """

    try:
        issues = jira.list_issues(
            project=args.project,
            component=args.component,
            reporter=args.reporter if args.reporter else None,
            assignee=args.assignee if not args.reporter else None,
        )

        if not issues:
            print("No issues found.")
            return []

        headers, rows = massage_issue_list(args, issues)
        format_and_print_rows(rows, headers, jira)

        return rows

    except ListIssuesError as e:
        msg = f"❌ Failed to list issues: {e}"
        print(msg)
        traceback.print_exc()  # Print the error traceback
        raise
