#!/usr/bin/env python
"""
A function to retrieve the active sprint using a provided request function.

The function 'get_sprint' takes a request function as an argument, which is used to make HTTP requests. It retrieves
the current active sprint information by making a GET request to the JIRA board API endpoint for active sprints.

:param request_fn: A function used to make HTTP requests. It should take two string arguments (HTTP method and path)
and return a dictionary.
:return: A dictionary containing the active sprint information.
"""

from typing import Callable, Dict

from core.env_fetcher import EnvFetcher


def get_sprint(request_fn: Callable[[str, str], Dict]) -> Dict:
    """
    Get the current active sprint.

    Arguments:
    - request_fn: A function that makes HTTP requests. It takes two string arguments (HTTP method and path) and returns
    a dictionary.

    Return:
    - A dictionary representing the current active sprint fetched using the provided request function.
    """
    board_number: str = EnvFetcher.get("JIRA_BOARD_ID")
    path: str = f"/rest/agile/1.0/board/{board_number}/sprint?state=active"
    return request_fn("GET", path)
