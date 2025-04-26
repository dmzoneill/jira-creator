#!/usr/bin/env python
"""
A function to retrieve the active sprint using a provided request function.

:param request_fn: A function used to make HTTP requests.
:return: A dictionary containing the active sprint information.
"""

from core.env_fetcher import EnvFetcher


def get_sprint(request_fn) -> dict:
    """
    Get the current active sprint.

    Arguments:
    - self: The object instance.

    Return:
    - The result the current active sprint.
    """
    board_number = EnvFetcher.get("JIRA_BOARD_ID")
    path = f"/rest/agile/1.0/board/{board_number}/sprint?state=active"
    return request_fn("GET", path)
