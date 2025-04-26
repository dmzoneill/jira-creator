#!/usr/bin/env python
"""
This script defines a function clone_issue that sends a POST request to clone an issue in a Jira instance.
The function takes a request function and an issue key as parameters and returns the response as a dictionary.

Functions:
- clone_issue: Sends a POST request to clone an issue in a Jira instance using the provided request function and issue
key.

Imports:
- Callable: Type hint for a callable.
- Dict: Type hint for a dictionary.
"""
from typing import Callable, Dict


def clone_issue(request_fn: Callable[[str, str, Dict], Dict], issue_key: str) -> Dict:
    """
    Clone an issue by creating a new issue with the same details as the specified issue.

    Arguments:
    - request_fn (Callable): A function that sends HTTP requests. It takes HTTP method, path, and JSON data as
    parameters.
    - issue_key (str): The key of the issue to be cloned.

    Return:
    - Dict: A dictionary representing the newly created issue.

    """
    path = f"/rest/api/2/issue/{issue_key}/flags"
    return request_fn("POST", path, json_data={})
