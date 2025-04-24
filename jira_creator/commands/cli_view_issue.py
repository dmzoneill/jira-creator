#!/usr/bin/env python
"""
This script defines a function cli_view_issue that retrieves and displays information about a Jira issue. It handles
custom fields by replacing their keys with their real names using a helper function from the Jira object. The function
then sorts and prints the issue details. If an exception ViewIssueError is raised during the process, it catches the
exception, prints an error message, and raises the exception again.

Function cli_view_issue:
- View a specific issue in JIRA.
- Arguments:
- jira: A JIRA client object used to interact with the JIRA API.
- args: A dictionary containing the following key:
- issue_key: A string representing the key of the issue to be viewed.
- Exceptions:
- This function may raise exceptions if there are issues with accessing or viewing the specified issue in JIRA.
- Note:
- This function retrieves and displays information about a specific issue in JIRA using the provided JIRA client object.
"""

from exceptions.exceptions import ViewIssueError


def cli_view_issue(jira, args):
    """
    View a specific issue in JIRA.

    Arguments:
    - jira: A JIRA client object used to interact with the JIRA API.
    - args: A dictionary containing the following key:
    - issue_key: A string representing the key of the issue to be viewed.

    Exceptions:
    - This function may raise exceptions if there are issues with accessing or viewing the specified issue in JIRA.

    Note:
    - This function retrieves and displays information about a specific issue in JIRA using the provided JIRA client
    object.
    """

    try:
        issue = jira.view_issue(args.issue_key)

        # Create a new dictionary with real names as keys
        updated_issue = {}

        for key in issue:
            # Check if the key is a custom field
            if "customfield" in key:
                real_name = jira.get_field_name(key)
                updated_issue[real_name] = issue[key]
            else:
                # For non-custom fields, keep the original key
                updated_issue[key] = issue[key]

        # Sort the dictionary by the real names (keys)
        for key in sorted(updated_issue.keys()):
            print(f"{key} : {updated_issue[key]}")

        return issue
    except ViewIssueError as e:
        msg = f"❌ Unable to view issue: {e}"
        print(msg)
        raise ViewIssueError(e) from e
