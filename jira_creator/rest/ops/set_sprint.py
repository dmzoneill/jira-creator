#!/usr/bin/env python
"""
This script defines a function set_sprint that updates the sprint field of a JIRA issue using the provided request
function, issue key, and sprint ID. It constructs a payload with the sprint information and makes a PUT request to the
JIRA API endpoint to update the issue. The sprint ID can be None to remove the issue from the sprint. The function
relies on the EnvFetcher class from core.env_fetcher to retrieve the JIRA sprint field name.

The set_sprint function takes three arguments:
- request_fn (function): A function used to make HTTP requests.
- issue_key (str): The key of the Jira issue to update.
- sprint_id (int): The ID of the sprint to set for the issue. If sprint_id is not provided (or 0), the issue will
be removed from any sprint.

Side Effects:
- Modifies the sprint field of the specified Jira issue.
"""

from typing import Any, Callable, Dict

from core.env_fetcher import EnvFetcher


def set_sprint(
    request_fn: Callable[[str, str, Dict[str, Any]], None],
    issue_key: str,
    sprint_id: int,
) -> None:
    """
    Set the sprint for a specific Jira issue.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the Jira issue to update.
    - sprint_id (int): The ID of the sprint to set for the issue. If sprint_id is not provided (or 0), the issue will
    be removed from any sprint.

    Side Effects:
    - Modifies the sprint field of the specified Jira issue.
    """

    payload: Dict[str, Any] = {
        "fields": {
            EnvFetcher.get("JIRA_SPRINT_FIELD"): (
                None if not sprint_id else [str(sprint_id)]
            )
        }
    }

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json_data=payload,
    )
