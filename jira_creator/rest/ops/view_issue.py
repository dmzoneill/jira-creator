#!/usr/bin/env python
"""
Retrieves and returns the fields of a specific issue using the provided request function.

Arguments:
- request_fn (function): A function used to make HTTP requests.
- issue_key (str): The key identifying the specific issue to retrieve.

Return:
- dict: A dictionary containing the fields of the specified issue.
"""


def view_issue(request_fn, issue_key):
    """
    Retrieves and returns the fields of a specific issue using the provided request function.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key identifying the specific issue to retrieve.

    Return:
    - dict: A dictionary containing the fields of the specified issue.
    """

    return request_fn("GET", f"/rest/api/2/issue/{issue_key}")["fields"]
