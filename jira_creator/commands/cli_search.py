#!/usr/bin/env python
"""
This module provides a command-line interface (CLI) function for searching JIRA issues using JIRA Query Language (JQL).

The `cli_search` function allows users to search for issues based on a specified JQL query through a JIRA client
instance. It retrieves relevant issue fields and displays the results in a formatted table. The function includes error
handling for search-related exceptions to ensure appropriate messages are displayed when issues arise.

Functions:
- cli_search(jira, args): Executes a search for issues in JIRA using the provided JQL query.

Arguments:
- jira: A JIRA client object for API communication.
- args: An object containing parsed command-line arguments, which must include a 'jql' attribute representing the JQL
query.

Exceptions:
- The function may raise exceptions related to the JIRA API or invalid queries.

Note:
- This script depends on external modules such as 'core.env_fetcher' and 'exceptions.exceptions' for environment
variable fetching and exception handling, respectively.
"""

# pylint: disable=too-many-statements too-many-branches

from argparse import Namespace
from typing import Any, List, Union

from core.view_helpers import format_and_print_rows, massage_issue_list
from exceptions.exceptions import SearchError
from rest.client import JiraClient


# /* jscpd:ignore-start */
def cli_search(jira: JiraClient, args: Namespace) -> Union[List[Any], bool]:
    """
    Search for issues in Jira based on the provided JQL query.

    Arguments:
    - jira: A Jira client object used to communicate with the Jira API.
    - args: An object containing the parsed command-line arguments.
    It should have a 'jql' attribute representing the Jira Query Language query.

    Exceptions:
    - This function may raise exceptions related to the Jira API or invalid queries.

    Note: This function interacts with the Jira API to search for issues based on the provided JQL query.
    """

    try:
        jql: str = args.jql
        issues: List[dict] = jira.search_issues(jql)

        if issues is None or len(issues) == 0:
            print("❌ No issues found for the given JQL.")
            return False

        headers, rows = massage_issue_list(args, issues)
        format_and_print_rows(rows, headers, jira)

        return rows

    except SearchError as e:
        msg = f"❌ Failed to search issues: {e}"
        print(msg)
        raise SearchError(e) from e


# /* jscpd:ignore-end */
