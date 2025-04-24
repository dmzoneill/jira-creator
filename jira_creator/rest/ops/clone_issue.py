#!/usr/bin/env python
"""
Clones an issue by creating a new flag for the specified issue key.

Arguments:
- request_fn (function): A function used to make HTTP requests.
- issue_key (str): The key of the issue to be cloned.

Return:
- dict: A dictionary representing the response from the request function.
"""


def clone_issue(request_fn, issue_key) -> dict:
    """
    Clones an issue by creating a new flag for the specified issue key.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the issue to be cloned.

    Return:
    - dict: A dictionary representing the response from the request function.
    """

    path = f"/rest/api/2/issue/{issue_key}/flags"
    # payload = {"flag": flag_name}
    return request_fn("POST", path, json={})
