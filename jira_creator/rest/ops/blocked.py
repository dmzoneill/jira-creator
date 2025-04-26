#!/usr/bin/env python
"""
This module provides functionality to retrieve and filter blocked issues from a list of issues based on specified
criteria. The primary function, `blocked`, identifies blocked issues by checking a specific field value and constructs
a dictionary with key details for each blocked issue. It accepts a callable function to fetch issues and optional
parameters for project, component, and assignee, returning a list of dictionaries containing details of the blocked
issues.

Function `blocked`:
- Retrieves a list of blocked issues based on specified project, component, and assignee.

Arguments:
- list_issues_fn (Callable[..., List[Dict[str, Any]]]): A function that returns a list of issues filtered by project,
component, and assignee.
- project (Optional[str]): The project name to filter issues. Defaults to None.
- component (Optional[str]): The component name to filter issues. Defaults to None.
- assignee (Optional[str]): The assignee name to filter issues. Defaults to None.

Returns:
- List[Dict[str, Any]]: List of dictionaries containing details of blocked issues.

Side Effects:
- Modifies the 'issues' list by populating it with the filtered list of blocked issues.
"""

# pylint: disable=duplicate-code

from typing import Any, Callable, Dict, List, Optional

from core.env_fetcher import EnvFetcher


def blocked(
    list_issues_fn: Callable[..., List[Dict[str, Any]]],
    project: Optional[str] = None,
    component: Optional[str] = None,
    assignee: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve a list of blocked issues based on specified project, component, and assignee.

    Arguments:
    - list_issues_fn (Callable[..., List[Dict[str, Any]]): A function that returns a list of issues based on project,
    component, and assignee parameters.
    - project (Optional[str]): The project name to filter the issues. Defaults to None.
    - component (Optional[str]): The component name to filter the issues. Defaults to None.
    - assignee (Optional[str]): The assignee name to filter the issues. Defaults to None.

    Return:
    - List[Dict[str, Any]]: List of dictionaries containing details of blocked issues.

    Side Effects:
    - Modifies the 'issues' list by populating it with the filtered list of issues.
    """

    issues: List[Dict[str, Any]] = list_issues_fn(
        project=project, component=component, assignee=assignee
    )

    blocked_issues: List[Dict[str, Any]] = []
    for issue in issues:
        fields: Dict[str, Any] = issue["fields"]
        is_blocked: bool = (
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
