#!/usr/bin/env python
"""
Remove a flag from a specific issue on a Jira board.

This script defines a function 'remove_flag' that takes two arguments:
- request_fn: A function used to make HTTP requests.
- issue_key: The key of the issue from which the flag should be removed.

The function sends a POST request to remove the flag from the specified issue on the Jira board.

Returns:
- dict: A dictionary containing the response data from the request.
"""


from typing import Callable


def remove_flag(request_fn: Callable[[str, str, dict], dict], issue_key: str) -> dict:
    """
    Remove a flag from a specific issue on a Jira board.

    Arguments:
    - request_fn (Callable[[str, str, dict], dict]): A function used to make HTTP requests.
    - issue_key (str): The key of the issue from which the flag should be removed.

    Return:
    - dict: A dictionary containing the response data from the request.
    """

    path: str = "/rest/greenhopper/1.0/xboard/issue/flag/flag.json"
    payload: dict = {"issueKeys": [issue_key]}
    return request_fn("POST", path, json_data=payload)
