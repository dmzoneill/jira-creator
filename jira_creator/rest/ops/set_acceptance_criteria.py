#!/usr/bin/env python
"""
This script defines a function set_acceptance_criteria that updates the acceptance criteria of a JIRA issue. It takes
three parameters: request_fn, issue_key, and acceptance_criteria. The function constructs a payload with the acceptance
criteria data and performs a PUT request to update the issue in JIRA. It also prints a success message after updating
the acceptance criteria.

The set_acceptance_criteria function takes three arguments:
- request_fn (function): A function used to make HTTP requests.
- issue_key (str): The key of the JIRA issue to set acceptance criteria for.
- acceptance_criteria (str): The acceptance criteria to set for the JIRA issue.
"""

from typing import Callable

from core.env_fetcher import EnvFetcher


def set_acceptance_criteria(
    request_fn: Callable[[str, str, dict], None],
    issue_key: str,
    acceptance_criteria: str,
) -> None:
    """
    Set acceptance criteria for a JIRA issue.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the JIRA issue to set acceptance criteria for.
    - acceptance_criteria (str): The acceptance criteria to set for the JIRA issue.
    """

    payload = {
        "fields": {
            EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD"): (
                "" if not acceptance_criteria else str(acceptance_criteria)
            )
        }
    }

    # Perform the PUT request to update the acceptance criteria
    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json_data=payload,
    )

    print(f"✅ Updated acceptance criteria of {issue_key}")
