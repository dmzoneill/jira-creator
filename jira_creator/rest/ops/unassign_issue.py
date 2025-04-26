#!/usr/bin/env python
"""
This module provides a function to unassign an issue in Jira by sending a PUT request to the Jira API.
If successful, it returns True. If an error occurs during the unassignment process, it raises an UnassignIssueError.

The unassign_issue function unassigns the assignee from a specified issue.

Arguments:
- request_fn (function): A function used to make API requests.
- issue_key (str): The key of the issue to unassign.

Return:
- bool: True if the issue was successfully unassigned.

Exceptions:
- UnassignIssueError: Raised if there is an issue with unassigning the specified issue.
"""

from typing import Callable

from exceptions.exceptions import UnassignIssueError


def unassign_issue(
    request_fn: Callable[[str, str, dict], None], issue_key: str
) -> bool:
    """
    Unassigns the assignee from a specified issue.

    Arguments:
    - request_fn (function): A function used to make API requests.
    - issue_key (str): The key of the issue to unassign.

    Return:
    - bool: True if the issue was successfully unassigned.

    Exceptions:
    - UnassignIssueError: Raised if there is an issue with unassigning the specified issue.
    """

    try:
        request_fn(
            "PUT",
            f"/rest/api/2/issue/{issue_key}",
            json_data={"fields": {"assignee": None}},
        )
        return True
    except UnassignIssueError as e:
        msg = f"❌ Failed to unassign issue {issue_key}: {e}"
        print(msg)
        raise UnassignIssueError(e) from e
