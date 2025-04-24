#!/usr/bin/env python
"""
Add a flag to an issue on a board.

Arguments:
- request_fn (function): A function used to make HTTP requests.
- issue_keys (str): The key of the issue to add the flag to.

Return:
- dict: A dictionary containing the response from the HTTP POST request.
"""


def add_flag(request_fn, issue_keys) -> dict:
    """
    Add a flag to an issue on a board.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_keys (str): The key of the issue to add the flag to.

    Return:
    - dict: A dictionary containing the response from the HTTP POST request.
    """

    path = "/rest/greenhopper/1.0/xboard/issue/flag/flag.json"
    payload = {"issueKeys": [issue_keys], "flag": True}
    return request_fn("POST", path, json=payload)
