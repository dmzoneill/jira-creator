#!/usr/bin/env python
"""
This module provides a function to remove an issue from the current sprint backlog.

Functions:
- remove_from_sprint: Removes an issue from the current sprint backlog.

Exceptions:
- RemoveFromSprintError: Raised when there is an issue removing the specified issue from the sprint backlog.

Side Effects:
- If successful, prints a message indicating that the issue has been moved to the backlog.
- If an error occurs, prints a message indicating the failure and raises a RemoveFromSprintError.
"""
from typing import Callable

from exceptions.exceptions import RemoveFromSprintError


def remove_from_sprint(
    request_fn: Callable[[str, str, dict], None], issue_key: str
) -> None:
    """
    Removes an issue from the current sprint backlog.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the issue to be removed from the sprint backlog.

    Exceptions:
    - RemoveFromSprintError: Raised when there is an issue removing the specified issue from the sprint backlog.

    Side Effects:
    - If successful, prints a message indicating that the issue has been moved to the backlog.
    - If an error occurs, prints a message indicating the failure and raises a RemoveFromSprintError.
    """

    try:
        request_fn(
            "POST",
            "/rest/agile/1.0/backlog/issue",
            json_data={"issues": [issue_key]},
        )
        print(f"✅ Moved {issue_key} to backlog")
    except RemoveFromSprintError as e:
        msg = f"❌ Failed to remove from sprint: {e}"
        print(msg)
        raise RemoveFromSprintError(e) from e
