#!/usr/bin/env python
"""
This module contains a function to search for JIRA issues based on a JQL query.

The 'search_issues' function takes two parameters: 'request_fn' for making HTTP requests and 'jql' for the JIRA Query
Language query.
It constructs the necessary parameters for the JIRA API request, including specific fields to retrieve.
The function then retrieves a list of issues matching the JQL query and processes each issue to extract sprint
information.
If an issue is associated with an active sprint, it updates the issue with the active sprint name; otherwise, it sets
the sprint as 'No active sprint'.
The function returns a list of processed issues.

Note: This function relies on the 'EnvFetcher' class from 'core.env_fetcher' for fetching environment variables related
to JIRA fields.
"""

# pylint: disable=duplicate-code too-many-locals

import re
from typing import Callable, List, Dict, Any

from core.env_fetcher import EnvFetcher


def search_issues(request_fn: Callable[[str, str, Dict[str, Any]], Dict[str, Any]], jql: str) -> List[Dict[str, Any]]:
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

    issues: List[Dict[str, Any]] = request_fn("GET", "/rest/api/2/search", params=params).get("issues", [])

    name_regex: str = r"name\s*=\s*([^,]+)"
    state_regex: str = r"state\s*=\s*([A-Za-z]+)"

    for issue in issues:
        sprints: List[str] = issue.get("fields", {}).get(EnvFetcher.get("JIRA_SPRINT_FIELD"), [])

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