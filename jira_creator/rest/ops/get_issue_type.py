#!/usr/bin/env python
"""
This module includes a function 'get_issue_type' that retrieves the type of an issue from a Jira instance.
The function takes two parameters:
- request_fn: a Callable that sends a request to the Jira API and returns a dictionary response.
- issue_key: a string representing the key of the issue to retrieve.

The function returns a string representing the type of the issue.
"""
from typing import Callable


def get_issue_type(request_fn: Callable[[str, str], dict], issue_key: str) -> str:
    """
    Retrieve the type of an issue from Jira.

    Arguments:
    - request_fn (Callable[[str, str], dict]): A function that makes a request to the Jira API. It takes two
    parameters: HTTP method (e.g., "GET") and the API endpoint. It returns a dictionary representing the API response.
    - issue_key (str): The key of the issue to retrieve the type for.

    Return:
    - str: The name of the issue type associated with the specified issue key.

    """
    issue = request_fn("GET", f"/rest/api/2/issue/{issue_key}")
    return issue["fields"]["issuetype"]["name"]
