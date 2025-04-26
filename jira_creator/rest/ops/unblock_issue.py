#!/usr/bin/env python
"""
Defines a function to unblock a Jira issue by updating specific fields.
The function 'unblock_issue' takes a request function, issue key, and updates the Jira issue fields.
Parameters:
- request_fn: A callable function to make the request with method, URL, and JSON payload.
- issue_key: A string representing the key of the Jira issue to unblock.
Returns:
- None
"""
from typing import Callable

from core.env_fetcher import EnvFetcher


def unblock_issue(request_fn: Callable[[str, str, dict], None], issue_key: str) -> None:
    """
    Unblocks a JIRA issue by updating specific fields to mark it as unblocked.

    Arguments:
    - request_fn (Callable[[str, str, dict], None]): A function to make HTTP requests. Takes HTTP method, URL, and JSON
    data as parameters.
    - issue_key (str): The key of the JIRA issue to unblock.

    Side Effects:
    - Modifies the specified JIRA issue by updating the blocked field and reason field to mark it as unblocked.
    """
    blocked_field: str = EnvFetcher.get("JIRA_BLOCKED_FIELD")
    reason_field: str = EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD")

    payload: dict = {"fields": {blocked_field: {"value": False}, reason_field: ""}}

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json_data=payload,
    )
