#!/usr/bin/env python
"""
This module provides a function to list JIRA issues based on specified criteria.

The `list_issues` function allows users to filter JIRA issues using various parameters such as project, component,
assignee, status, summary, and others. It constructs a JQL (JIRA Query Language) query based on the provided parameters
and retrieves the relevant issues through the JIRA API.

Additionally, the function processes the retrieved issues to extract sprint information, adding it to each issue before
returning the list of filtered issues.

Note: The function includes JSCPD ignore comments to exclude code blocks from duplication detection.
"""

# pylint: disable=too-many-arguments too-many-positional-arguments too-many-locals

import re
from typing import Any, Callable, Dict, List, Optional

from core.env_fetcher import EnvFetcher


# /* jscpd:ignore-start */
def list_issues(
    request_fn: Callable[..., Dict[str, Any]],
    get_current_user_fn: Callable[[], str],
    project: Optional[str] = None,
    component: Optional[str] = None,
    assignee: Optional[str] = None,
    status: Optional[str] = None,
    summary: Optional[str] = None,
    issues_blocked: bool = False,
    issues_unblocked: bool = False,
    reporter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve a list of issues based on specified filters.

    Arguments:
    - request_fn (Callable[..., Dict[str, Any]]): A function used to make HTTP requests.
    - get_current_user_fn (Callable[[], str]): A function used to retrieve the current user.
    - project (Optional[str], optional): Filter issues by project name.
    - component (Optional[str], optional): Filter issues by component name.
    - assignee (Optional[str], optional): Filter issues by assignee.
    - status (Optional[str], optional): Filter issues by status.
    - summary (Optional[str], optional): Filter issues by summary.
    - issues_blocked (bool, optional): Flag to filter blocked issues.
    - issues_unblocked (bool, optional): Flag to filter unblocked issues.
    - reporter (Optional[str], optional): Filter issues by reporter.

    Returns:
    - List[Dict[str, Any]]: A list of dictionaries representing the filtered issues. Each dictionary contains
    information about the issue, including key, summary, status, assignee, priority, story points, sprint, and blocked
    status.
    """

    jql_parts: List[str] = []
    jql_parts.append(f'project="{project}"')
    jql_parts.append(f'component="{component}"')

    if not reporter:
        assignee = assignee if assignee is not None else get_current_user_fn()
        jql_parts.append(f'assignee="{assignee}"')
    if reporter:
        jql_parts.append(f'reporter="{reporter}"')
    if status:
        jql_parts.append(f'status="{status}"')
    if summary:
        jql_parts.append(f'summary~"{summary}"')
    if issues_blocked:
        jql_parts.append(EnvFetcher.get("JIRA_BLOCKED_FIELD") + '="True"')
    if issues_unblocked:
        jql_parts.append(EnvFetcher.get("JIRA_BLOCKED_FIELD") + '!="True"')

    jql: str = (
        " AND ".join(jql_parts) + ' AND status NOT IN ("Closed", "Done", "Cancelled")'
    )

    fields: List[Dict[str, Any]] = request_fn("GET", "/rest/api/2/field")
    field_names: List[str] = [field["id"] for field in fields]
    field_names = [name for name in field_names if "custom" not in name]
    field_names += [
        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"),
        EnvFetcher.get("JIRA_SPRINT_FIELD"),
        EnvFetcher.get("JIRA_BLOCKED_FIELD"),
    ]
    field_names += ["key"]

    params: Dict[str, Any] = {
        "jql": jql,
        "fields": ",".join(field_names),
        "maxResults": 200,
    }
    issues: List[Dict[str, Any]] = request_fn(
        "GET", "/rest/api/2/search", params=params
    ).get("issues", [])

    name_regex: str = r"name\s*=\s*([^,]+)"
    state_regex: str = r"state\s*=\s*([A-Za-z]+)"

    for issue in issues:
        sprints: List[str] = issue.get("fields", {}).get(
            EnvFetcher.get("JIRA_SPRINT_FIELD"), []
        )
        if sprints is None:
            sprints = []

        active_sprint: Optional[str] = None
        for sprint_str in sprints:
            name_match = re.search(name_regex, sprint_str)
            sprint_name: Optional[str] = name_match.group(1) if name_match else None

            state_match = re.search(state_regex, sprint_str)
            sprint_state: Optional[str] = state_match.group(1) if state_match else None

            if sprint_state == "ACTIVE" and sprint_name:
                active_sprint = sprint_name
                break

        issue["sprint"] = active_sprint if active_sprint else "No active sprint"

    return issues

    # /* jscpd:ignore-end */
