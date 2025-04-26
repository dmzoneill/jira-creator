#!/usr/bin/env python
"""
This module provides functionality to retrieve and filter blocked issues from a list of issues based on specified
criteria.
The primary function, `blocked`, takes a function that returns a list of issues and optional parameters for project,
component, and assignee. It identifies blocked issues by checking a specific field value and constructs a dictionary
with key details for each blocked issue. The function returns a list of these dictionaries.

Function `blocked`:
- Retrieves a list of blocked issues based on specified project, component, and assignee.

Arguments:
- list_issues_fn (function): A function that returns a list of issues filtered by project, component, and assignee.
- project (str): The project name to filter issues. Defaults to None.
- component (str): The component name to filter issues. Defaults to None.
- assignee (str): The assignee name to filter issues. Defaults to None.

Returns:
- List of dictionaries containing details of blocked issues.

Side Effects:
- Modifies the 'issues' list by populating it with the filtered list of blocked issues.
"""

# pylint: disable=duplicate-code

from core.env_fetcher import EnvFetcher


# /* jscpd:ignore-start */
def blocked(list_issues_fn, project=None, component=None, assignee=None):
    """
    Retrieve a list of blocked issues based on specified project, component, and assignee.

    Arguments:
    - list_issues_fn (function): A function that returns a list of issues based on project, component, and assignee
    parameters.
    - project (str): The project name to filter the issues. Defaults to None.
    - component (str): The component name to filter the issues. Defaults to None.
    - assignee (str): The assignee name to filter the issues. Defaults to None.

    Return:
    - List of dictionaries containing details of blocked issues.

    Side Effects:
    - Modifies the 'issues' list by populating it with the filtered list of issues.
    """

    issues = list_issues_fn(project=project, component=component, assignee=assignee)

    blocked_issues = []
    for issue in issues:
        fields = issue["fields"]
        is_blocked = (
            fields.get(EnvFetcher.get("JIRA_BLOCKED_FIELD"), {}).get("value") == "True"
        )
        if is_blocked:
            blocked_issues.append(
                {
                    "key": issue["key"],
                    "status": fields["status"]["name"],
                    "assignee": (
                        fields["assignee"]["displayName"]
                        if fields["assignee"]
                        else "Unassigned"
                    ),
                    "reason": fields.get(
                        EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"), "(no reason)"
                    ),
                    "summary": fields["summary"],
                }
            )
    return blocked_issues


# /* jscpd:ignore-end */
