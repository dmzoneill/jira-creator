#!/usr/bin/env python
"""
A function to retrieve the description of a Jira issue using the provided request function and issue key.

Parameters:
request_fn (callable): A function used to make HTTP requests.
issue_key (str): The key of the Jira issue for which the description is to be retrieved.

Returns:
str: The description of the Jira issue corresponding to the provided issue key. Returns an empty string if no
description is found.
"""


def get_description(request_fn: callable, issue_key: str) -> str:
    """
    Retrieve the description of a specific issue from a Jira instance using the provided request function.

    Arguments:
    - request_fn (callable): A function used to make HTTP requests. It should accept HTTP method and endpoint
    parameters.
    - issue_key (str): The key of the issue for which the description should be retrieved.

    Return:
    - str: The description of the specified issue. If the description is not found, an empty string is returned.
    """
    return request_fn("GET", f"/rest/api/2/issue/{issue_key}")["fields"].get(
        "description", ""
    )
