#!/usr/bin/env python
"""
Retrieve the description of a specific issue from a Jira instance.

Arguments:
- request_fn (function): A function used to make HTTP requests. It should accept HTTP method and URL parameters.
- issue_key (str): The key of the issue for which the description is to be retrieved.

Return:
- str: The description of the specified issue. If the description is not available, an empty string is returned.
"""


def get_description(request_fn, issue_key):
    """
    Retrieve the description of a specific issue from a Jira instance.

    Arguments:
    - request_fn (function): A function used to make HTTP requests. It should accept HTTP method and URL parameters.
    - issue_key (str): The key of the issue for which the description is to be retrieved.

    Return:
    - str: The description of the specified issue. If the description is not available, an empty string is returned.
    """

    return request_fn("GET", f"/rest/api/2/issue/{issue_key}")["fields"].get(
        "description", ""
    )
