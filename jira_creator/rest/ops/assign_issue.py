#!/usr/bin/env python
"""
This module provides a function to assign an issue to a specific user using a given request function.

The assign_issue function takes three parameters:
- request_fn: a function to make a request (e.g., from requests library)
- issue_key: the key of the issue to be assigned
- assignee: the username of the user to whom the issue will be assigned

If successful, the function returns True. If an AssignIssueError is raised during the process, it prints an error
message and raises AssignIssueError with a custom message.
"""

from typing import Callable

from exceptions.exceptions import AssignIssueError


def assign_issue(
    request_fn: Callable[[str, str, dict], None], issue_key: str, assignee: str
) -> bool:
    """
    Assign the specified issue to the given assignee using the provided request function.

    Arguments:
    - request_fn (function): The function used to make HTTP requests.
    - issue_key (str): The key identifying the issue to be assigned.
    - assignee (str): The username of the user to whom the issue will be assigned.

    Return:
    - bool: True if the issue was successfully assigned.

    Exceptions:
    - AssignIssueError: Raised if there is an error while assigning the issue.

    Side Effects:
    - Makes an HTTP PUT request to assign the specified issue.
    - Prints an error message if the assignment fails.
    """

    try:
        request_fn(
            "PUT",
            f"/rest/api/2/issue/{issue_key}",
            json_data={"fields": {"assignee": {"name": assignee}}},
        )
        return True
    except AssignIssueError as e:
        msg = f"❌ Failed to assign issue {issue_key}: {e}"
        print(msg)
        raise AssignIssueError(e) from e
