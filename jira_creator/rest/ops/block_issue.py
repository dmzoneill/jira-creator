#!/usr/bin/env python
"""
Updates a JIRA issue by setting the blocked status and reason.

This module contains a function 'block_issue' that updates a specified JIRA issue by setting the blocked status and
reason for blocking. It takes the request function, JIRA issue key, and a reason as arguments to update the specified
issue.

Arguments:
- request_fn (function): The function used to make requests to JIRA.
- issue_key (str): The key of the JIRA issue to be updated.
- reason (str): The reason for blocking the JIRA issue.

Side Effects:
- Modifies the blocked status and reason fields of the specified JIRA issue.
"""
from typing import Callable

from core.env_fetcher import EnvFetcher


def block_issue(
    request_fn: Callable[[str, str, dict], None], issue_key: str, reason: str
) -> None:
    """
    Updates a JIRA issue by setting the blocked status and reason.

    Arguments:
    - request_fn (function): The function used to make requests to JIRA.
    - issue_key (str): The key of the JIRA issue to be updated.
    - reason (str): The reason for blocking the JIRA issue.

    Side Effects:
    - Modifies the blocked status and reason fields of the specified JIRA issue.
    """

    blocked_field = EnvFetcher.get("JIRA_BLOCKED_FIELD")
    reason_field = EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD")

    payload: dict = {}
    payload[blocked_field] = {}
    payload[blocked_field]["value"] = True
    payload[reason_field] = reason

    request_fn("PUT", f"/rest/api/2/issue/{issue_key}", json_data=payload)
