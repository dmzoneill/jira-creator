#!/usr/bin/env python
"""
A function to retrieve the active sprint using a provided request function.

:param request_fn: A function used to make HTTP requests.
:return: A dictionary containing the active sprint information.
"""

from core.env_fetcher import EnvFetcher
from typing import Callable, Dict


def get_sprint(request_fn: Callable[[str, str], Dict]) -> Dict:
    """
    Get the current active sprint.

    Arguments:
    - self: The object instance.

    Return:
    - The result the current active sprint.
    """
    board_number: str = EnvFetcher.get("JIRA_BOARD_ID")
    path: str = f"/rest/agile/1.0/board/{board_number}/sprint?state=active"
    return request_fn("GET", path)