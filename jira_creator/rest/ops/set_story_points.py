#!/usr/bin/env python
"""
This script defines a function set_story_points that updates the story points of a JIRA issue.
It takes three parameters: request_fn for making HTTP requests, issue_key for identifying the issue, and points for
specifying the new story points value.
The function constructs a payload with the new story points value and sends a PUT request to update the issue in JIRA
using the provided request_fn.
The JIRA field used for story points is fetched from the environment variables using the EnvFetcher class.

Function:
- set_story_points(request_fn, issue_key, points): Set the story points of a JIRA issue.

Arguments:
- request_fn (function): The function used to make requests to the JIRA API.
- issue_key (str): The key of the JIRA issue for which the story points need to be set.
- points (int): The number of story points to set for the issue.

Side Effects:
- Retrieves the JIRA story points field from the environment using EnvFetcher.

Note: This function is expected to continue with the logic to set the story points for the specified JIRA issue.
"""

from core.env_fetcher import EnvFetcher


def set_story_points(request_fn, issue_key, points):
    """
    Set the story points of a JIRA issue.

    Arguments:
    - request_fn (function): The function used to make requests to the JIRA API.
    - issue_key (str): The key of the JIRA issue for which the story points need to be set.
    - points (int): The number of story points to set for the issue.

    Side Effects:
    - Retrieves the JIRA story points field from the environment using EnvFetcher.

    Note: This function is expected to continue with the logic to set the story points for the specified JIRA issue.
    """

    field = EnvFetcher.get("JIRA_STORY_POINTS_FIELD")

    payload = {}
    payload["fields"] = {}
    payload["fields"][field] = points

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json_data=payload,
    )
