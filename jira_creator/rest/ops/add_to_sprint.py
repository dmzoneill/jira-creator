#!/usr/bin/env python
"""
This module provides a function to add an issue to a sprint in JIRA.

The function 'add_to_sprint_by_name' takes four parameters:
- request_fn: a function for making HTTP requests
- board_id: the ID of the JIRA board
- issue_key: the key of the issue to be added to the sprint
- sprint_name: the name of the sprint to which the issue will be added

If the 'board_id' is not provided, it raises an AddSprintError indicating that the JIRA_BOARD_ID is not set in the
environment.

It retrieves the list of sprints associated with the board using the 'request_fn' function, then finds the sprint ID
corresponding to the provided 'sprint_name'.

If the sprint ID is not found, it raises an AddSprintError indicating that the sprint with the provided name could not
be found.

Finally, it adds the 'issue_key' to the identified sprint using a POST request and prints a success message.

Note: This function assumes the 'request_fn' function is implemented elsewhere to handle HTTP requests.
"""

from typing import Any, Callable, Dict, List, Optional

from exceptions.exceptions import AddSprintError


def add_to_sprint(
    request_fn: Callable[[str, str, Dict[str, Any]], Dict[str, Any]],
    board_id: str,
    issue_key: str,
    sprint_name: str,
    assignee: str,
) -> None:
    """
    Add a specified sprint to a JIRA board using its name.

    Arguments:
    - request_fn (Callable[[str, str, Dict[str, Any]], Dict[str, Any]]): A function used to make HTTP requests.
    - board_id (str): The ID of the JIRA board to which the sprint will be added.
    - issue_key (str): The key of the JIRA issue to be added to the sprint.
    - sprint_name (str): The name of the sprint to be added to the board.
    - assignee (str): May be none or empty or a user to assign it to (default to current user).

    Exceptions:
    - AddSprintError: Raised when the 'board_id' is not provided in the environment variables.
    """

    if not board_id:
        raise AddSprintError("❌ JIRA_BOARD_ID not set in environment")

    sprints: List[Dict[str, Any]] = request_fn(
        "GET", f"/rest/agile/1.0/board/{board_id}/sprint"
    ).get("values", [])
    sprint_id: Optional[int] = next(
        (s["id"] for s in sprints if s["name"] == sprint_name), None
    )

    if not sprint_id:
        raise AddSprintError(f"❌ Could not find sprint named '{sprint_name}'")

    user: Dict[str, Any] = request_fn("GET", "/rest/api/2/myself")
    assignto = user.get("name") if assignee == "" or assignee is None else assignee

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json_data={"fields": {"assignee": {"name": assignto}}},
    )

    request_fn(
        "POST",
        f"/rest/agile/1.0/sprint/{sprint_id}/issue",
        json_data={"issues": [issue_key]},
    )
    print(f"✅ Added {issue_key} to sprint '{sprint_name}' on board {board_id}")
