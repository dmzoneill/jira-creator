#!/usr/bin/env python
"""
This module provides a function to search for JIRA issues using a specified JQL query.

The primary function, 'search_issues', accepts two arguments: 'request_fn', which is a callable used for making HTTP
requests, and 'jql', a string representing the JIRA Query Language query. The function constructs the necessary
parameters for querying the JIRA API, including fields to retrieve. It processes the returned issues to extract and
update sprint information, indicating whether each issue is associated with an active sprint or not. The function
ultimately returns a list of processed issues with relevant details.

Dependencies:
- The module relies on the 'EnvFetcher' class from 'core.env_fetcher' to retrieve environment variables related to
specific JIRA fields.

Usage:
- Call 'search_issues' with a valid request function and a JQL query to obtain a list of JIRA issues.
"""

# pylint: disable=duplicate-code too-many-locals

import re
from typing import Any, Callable, Dict, List

from core.env_fetcher import EnvFetcher


def search_issues(
    request_fn: Callable[[str, str, Dict[str, Any]], Dict[str, Any]], jql: str
) -> List[Dict[str, Any]]:
    """
    Search for issues in JIRA based on the provided JQL query.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - jql (str): JIRA Query Language (JQL) query to filter the search results.

    Return:
    - list: A list of dictionaries representing the searched JIRA issues. Each dictionary contains information about
    the issue, including summary, status, assignee, priority, story points, sprint, and blocked status.
    """

    fields: List[str] = request_fn("GET", "/rest/api/2/field")
    field_names: List[str] = [field["id"] for field in fields]
    field_names = [name for name in field_names if "custom" not in name]
    field_names += [
        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"),
        EnvFetcher.get("JIRA_SPRINT_FIELD"),
        EnvFetcher.get("JIRA_BLOCKED_FIELD"),
    ]
    field_names += ["key"]

    params: Dict[str, str] = {
        "jql": jql,
        "fields": ",".join(field_names),
        "maxResults": "200",
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

        if not sprints:
            issue["fields"]["sprint"] = "No active sprint"
            continue

        active_sprint: str = None
        for sprint_str in sprints:
            name_match = re.search(name_regex, sprint_str)
            sprint_name: str = name_match.group(1) if name_match else None

            state_match = re.search(state_regex, sprint_str)
            sprint_state: str = state_match.group(1) if state_match else None

            if sprint_state == "ACTIVE" and sprint_name:
                active_sprint = sprint_name
                break

        issue["fields"]["sprint"] = (
            active_sprint if active_sprint else "No active sprint"
        )

    return issues
