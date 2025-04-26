#!/usr/bin/env python
"""
Set the story points of a JIRA issue.

This file contains a function `set_story_points` that takes a request function, JIRA issue key, and story points as
arguments to set the story points for a specified JIRA issue. The function retrieves the JIRA story points field from
the environment using the `EnvFetcher` class. It then constructs a payload with the story points information and makes
a PUT request to the JIRA API to update the issue with the new story points.

Arguments:
- request_fn (function): The function used to make requests to the JIRA API.
- issue_key (str): The key of the JIRA issue for which the story points need to be set.
- points (int): The number of story points to set for the issue.

Side Effects:
- Retrieves the JIRA story points field from the environment using EnvFetcher.

Note: This function is expected to continue with the logic to set the story points for the specified JIRA issue.
"""
from typing import Callable

from core.env_fetcher import EnvFetcher


def set_story_points(
    request_fn: Callable[[str, str, dict], None], issue_key: str, points: int
) -> None:
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

    payload: dict = {}
    payload["fields"] = {}
    payload["fields"][field] = points

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json_data=payload,
    )
