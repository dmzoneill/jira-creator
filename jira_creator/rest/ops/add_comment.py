#!/usr/bin/env python
"""
Sends a POST request to add a comment to a specific issue in Jira.

Arguments:
- request_fn (function): A function used to send HTTP requests.
- issue_key (str): The key of the issue to which the comment will be added.
- comment (str): The text of the comment to be added.

Return:
- dict: A dictionary representing the response of the POST request.

Exceptions:
- None
"""
from typing import Callable, Dict


def add_comment(
    request_fn: Callable[[str, str, dict], Dict], issue_key: str, comment: str
) -> Dict:
    """
    Sends a POST request to add a comment to a specific issue in Jira.

    Arguments:
    - request_fn (function): A function used to send HTTP requests.
    - issue_key (str): The key of the issue to which the comment will be added.
    - comment (str): The text of the comment to be added.

    Return:
    - dict: A dictionary representing the response of the POST request.

    Exceptions:
    - None
    """

    path = f"/rest/api/2/issue/{issue_key}/comment"
    payload = {"body": comment}
    return request_fn("POST", path, json_data=payload)
