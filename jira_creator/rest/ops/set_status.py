#!/usr/bin/env python
"""
This module provides functionality to update the status of issues in a Jira system through a specified request function.

Functions:
- set_status(request_fn, issue_key, target_status): Updates the status of a specified issue to the desired target
status by making appropriate API calls.

Exceptions:
- SetStatusError: Custom exception raised when the target status cannot be found in the available transitions for the
issue.

Notes:
- The request function must be capable of making HTTP requests to the Jira API.
- The module includes logic to handle special cases, such as moving an issue to the top of the backlog or its parent
Epic when the target status is "refinement".
"""

# pylint: disable=too-many-locals

from typing import Any, Callable, Dict

from core.env_fetcher import EnvFetcher
from exceptions.exceptions import SetStatusError


def set_status(
    request_fn: Callable[[str, str, Dict[str, Any]], Dict[str, Any]],
    issue_key: str,
    target_status: str,
) -> None:
    """
    Retrieve the available transitions for a given issue and set its status to a target status.

    Arguments:
    - request_fn (Callable[[str, str, Dict[str, Any]], Dict[str, Any]]): A function used to make HTTP requests.
    - issue_key (str): The key identifying the issue to update.
    - target_status (str): The desired status to set for the issue.

    Returns:
    This function does not return anything.

    Exceptions:
    - SetStatusError: Raised if the target status is not found in the available transitions.

    Side Effects:
    - Modifies the status of the specified issue.
    - Prints the available transitions if the target status is not found.
    - Prints a success message after changing the status of the issue.
    """

    transitions: list[Dict[str, Any]] = request_fn(
        "GET", f"/rest/api/2/issue/{issue_key}/transitions"
    ).get("transitions", [])

    transition_id: str | None = next(
        (t["id"] for t in transitions if t["name"].lower() == target_status.lower()),
        None,
    )

    if not transition_id:
        print("Valid Transitions:")
        for t in transitions:
            print(t["name"])
        raise SetStatusError(f"❌ Transition to status '{target_status}' not found")

    # If the status is "refinement", we need to move the issue to the top of the backlog
    if target_status.lower() == "refinement":
        # Step 1: Get the backlog issues
        backlog_url: str = "/rest/greenhopper/1.0/xboard/plan/backlog/data.json"
        params: Dict[str, Any] = {
            "rapidViewId": EnvFetcher.get("JIRA_BOARD_ID"),
            "selectedProjectKey": EnvFetcher.get("PROJECT_KEY"),
        }
        backlog_response: Dict[str, Any] = request_fn("GET", backlog_url, params=params)
        backlog_issues: list[Dict[str, Any]] = backlog_response.get("issues", [])

        # Step 2: Get the first issue in the backlog (top of the backlog)
        if backlog_issues:
            first_backlog_issue_key: str = backlog_issues[0]["key"]

            # Step 3: Call the rank endpoint to move the current issue to the top
            rank_url: str = "/rest/greenhopper/1.0/sprint/rank"
            rank_payload: Dict[str, Any] = {
                "idOrKeys": [issue_key],
                "customFieldId": 12311940,  # Unknown magic number
                "rapidViewId": EnvFetcher.get("JIRA_BOARD_ID"),
                "calculateNewIssuesOrder": False,
                "sprintId": None,
                "addToBacklog": True,
                "idOrKeyBefore": first_backlog_issue_key,
            }
            request_fn("PUT", rank_url, json_data=rank_payload)
            print(f"✅ Moved {issue_key} to the top of the backlog")

        # Step 4: Check if the issue has a parent Epic
        issue_details_url: str = f"/rest/api/2/issue/{issue_key}"
        issue_details: Dict[str, Any] = request_fn("GET", issue_details_url)
        issue_id: str | None = issue_details.get("id")

        if EnvFetcher.get("JIRA_EPIC_FIELD") in issue_details.get("fields", {}):
            epic_key: str = issue_details.get("fields", {})[
                EnvFetcher.get("JIRA_EPIC_FIELD")
            ]

            # Step 5: Move the issue to the top of the Epic
            epic_rank_url: str = "/rest/greenhopper/1.0/rank/global/first"
            epic_rank_payload: Dict[str, Any] = {"issueId": issue_id}
            request_fn("POST", epic_rank_url, json_data=epic_rank_payload)
            print(f"✅ Moved {issue_key} to the top of its Epic {epic_key}")

    request_fn(
        "POST",
        f"/rest/api/2/issue/{issue_key}/transitions",
        json_data={"transition": {"id": transition_id}},
    )
    print(f"✅ Changed status of {issue_key} to '{target_status}'")
