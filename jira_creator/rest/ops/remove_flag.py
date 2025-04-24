#!/usr/bin/env python
"""
Remove a flag from a specific issue on a Jira board.

Arguments:
- request_fn (function): A function used to make HTTP requests.
- issue_key (str): The key of the issue from which the flag should be removed.

Return:
- dict: A dictionary containing the response data from the request.
"""


def remove_flag(request_fn, issue_key) -> dict:
    """
    Remove a flag from a specific issue on a Jira board.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the issue from which the flag should be removed.

    Return:
    - dict: A dictionary containing the response data from the request.
    """

    path = "/rest/greenhopper/1.0/xboard/issue/flag/flag.json"
    payload = {"issueKeys": [issue_key]}
    return request_fn("POST", path, json=payload)
