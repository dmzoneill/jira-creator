#!/usr/bin/env python
"""
This function sets a component for a given issue in Jira.

Parameters:
- request_fn (function): A function to make HTTP requests.
- issue_key (str): The key of the issue to set the component for.
- component (str): The name of the component to set for the issue.

Returns:
- dict: A dictionary representing the response from the HTTP request made to set the component for the issue.
"""


def set_component(request_fn, issue_key, component) -> dict:
    """
    Set a component for a specific issue identified by the given issue key.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the issue to which the component will be set.
    - component (str): The name of the component to set for the issue.

    Return:
    - dict: A dictionary representing the response from the HTTP request made to set the component for the issue.
    """
    path = f"/rest/api/2/issue/{issue_key}/components"
    payload = {"components": [{"name": component}]}
    return request_fn("PUT", path, json=payload)
