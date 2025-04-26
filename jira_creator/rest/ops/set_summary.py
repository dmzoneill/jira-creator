#!/usr/bin/env python
"""
Sets a summary for a specific issue in Jira.

Arguments:
- request_fn (function): A function used to make HTTP requests.
- issue_key (str): The key of the issue for which the summary will be set.
- summary (str): The new summary.

Return:
- dict: A dictionary containing the response from the HTTP POST request.
"""


def set_summary(request_fn: callable, issue_key: str, summary: str) -> dict:
    """
    Sets a summary for a specific issue in Jira.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the issue for which the summary will be set.
    - summary (str): The new summary.

    Return:
    - dict: A dictionary containing the response from the HTTP POST request.
    """

    # Define the path with the dynamic issue_key
    path = f"/rest/api/2/issue/{issue_key}"

    # Create the payload with the summary
    payload = {"fields": {"summary": summary}}

    # Make the POST request to update the issue summary
    return request_fn("PUT", path, json_data=payload)
