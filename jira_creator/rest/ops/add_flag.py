#!/usr/bin/env python
"""
Add a flag to an issue on a board.

This script defines a function 'add_flag' that adds a flag to a specified issue on a board. It takes two arguments:
- request_fn (function): A function used to make HTTP requests.
- issue_keys (str): The key of the issue to add the flag to.

The function returns a dictionary containing the response from the HTTP POST request.
"""
from typing import Callable, Dict


def add_flag(request_fn: Callable[[str, str, dict], Dict], issue_keys: str) -> Dict:
    """
    Add a flag to an issue on a board.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_keys (str): The key of the issue to add the flag to.

    Return:
    - dict: A dictionary containing the response from the HTTP POST request.
    """

    path: str = "/rest/greenhopper/1.0/xboard/issue/flag/flag.json"
    payload: dict = {"issueKeys": [issue_keys], "flag": True}
    return request_fn("POST", path, json_data=payload)
