#!/usr/bin/env python
"""
This module provides a function to retrieve information about a specific issue from a REST API.

The view_issue function takes two parameters:
- request_fn: a Callable that makes a request to the REST API with the HTTP method and endpoint
- issue_key: a string representing the key of the issue to retrieve

It returns a dictionary containing the fields of the requested issue.
"""
from typing import Any, Callable, Dict


def view_issue(
    request_fn: Callable[[str, str], Dict[str, Any]], issue_key: str
) -> Dict[str, Any]:
    """
    Retrieves information about a specific issue from a Jira instance.

    Arguments:
    - request_fn (Callable[[str, str], Dict[str, Any]): A function that makes HTTP requests to the Jira API.
    - issue_key (str): The key of the issue to retrieve information for.

    Return:
    - Dict[str, Any]: A dictionary containing the fields of the specified issue.

    Exceptions:
    - None
    """
    return request_fn("GET", f"/rest/api/2/issue/{issue_key}")["fields"]
