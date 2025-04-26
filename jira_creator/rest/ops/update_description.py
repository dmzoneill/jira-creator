#!/usr/bin/env python
"""
Updates the description of a Jira issue using the provided request function.

Arguments:
- request_fn (function): A function used to make HTTP requests.
- issue_key (str): The key of the Jira issue to update.
- new_description (str): The new description to set for the Jira issue.
"""

from typing import Callable

def update_description(request_fn: Callable[[str, str, dict], None], issue_key: str, new_description: str) -> None:
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