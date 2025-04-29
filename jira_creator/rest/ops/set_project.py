#!/usr/bin/env python
"""
A function to set the project for a specific issue in Jira.

Args:
- request_fn (function): A function used to send HTTP requests.
- issue_key (str): The key of the issue to update.
- project (str): The key of the project to set for the issue.

Returns:
- dict: A dictionary representing the response from the HTTP request.
"""


def set_project(request_fn, issue_key, project) -> dict:
    """
    Set the project of a specific issue.

    Arguments:
    - request_fn (function): A function used to send HTTP requests.
    - issue_key (str): The key of the issue to update.
    - project (str): The key of the project to set for the issue.

    Return:
    - dict: A dictionary representing the response from the HTTP request.
    """
    path = f"/rest/api/2/issue/{issue_key}"
    payload = {"fields": {"project": {"key": project}}}
    return request_fn("PUT", path, json=payload)
