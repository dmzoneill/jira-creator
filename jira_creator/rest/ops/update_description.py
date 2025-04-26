#!/usr/bin/env python
"""
Updates the description of a Jira issue using the provided request function.

This script defines a function 'update_description' that takes a request function, Jira issue key, and a new
description as arguments. It then makes a PUT request to update the description of the specified Jira issue by calling
the provided request function with the necessary parameters.

The 'update_description' function takes the following arguments:
- request_fn (function): A function used to make HTTP requests.
- issue_key (str): The key of the Jira issue to update.
- new_description (str): The new description to set for the Jira issue.
"""

from typing import Callable


def update_description(
    request_fn: Callable[[str, str, dict], None], issue_key: str, new_description: str
) -> None:
    """
    Updates the description of a Jira issue using the provided request function.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the Jira issue to update.
    - new_description (str): The new description to set for the Jira issue.
    """

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json_data={"fields": {"description": new_description}},
    )
