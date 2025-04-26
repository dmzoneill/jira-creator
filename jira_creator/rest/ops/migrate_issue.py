#!/usr/bin/env python
"""
This module provides a function to migrate an issue in Jira from one key to another.

The `migrate_issue` function takes four parameters:
- `request_fn`: A Callable that sends requests to the Jira API.
- `jira_url`: A string representing the base URL of the Jira instance.
- `build_payload_fn`: A Callable that builds the payload for creating a new issue.
- `old_key`: A string representing the key of the issue to be migrated.
- `new_type`: A string representing the type of the new issue.

The function retrieves the details of the old issue, creates a new issue with the provided type, and updates the old
issue with a comment indicating the migration. It also transitions the old issue to a final state if possible.

Returns the key of the newly created issue.
"""
from typing import Any, Callable, Dict


def migrate_issue(
    request_fn: Callable[[str, str, Dict[str, Any]], Dict[str, Any]],
    jira_url: str,
    build_payload_fn: Callable[[str, str, str], Dict[str, Any]],
    old_key: str,
    new_type: str,
) -> str:
    """
    Migrates an issue from one type to another in Jira by creating a new issue and updating the old one.

    Arguments:
    - request_fn (Callable): A function for making HTTP requests with parameters (method, endpoint, data).
    - jira_url (str): The base URL of the Jira instance.
    - build_payload_fn (Callable): A function for constructing the payload for creating a new issue.
    - old_key (str): The key of the issue to be migrated.
    - new_type (str): The type of the new issue to be created.

    Returns:
    - str: The key of the newly created issue.

    Side Effects:
    - Creates a new issue in Jira based on the provided parameters.
    - Updates the description of the old issue with migration information.
    - Moves the old issue to a transition status if applicable.

    """
    fields = request_fn("GET", f"/rest/api/2/issue/{old_key}")["fields"]
    summary = fields.get("summary", f"Migrated from {old_key}")
    description = fields.get("description", f"Migrated from {old_key}")

    payload = build_payload_fn(summary, description, new_type)
    new_key = request_fn("POST", "/rest/api/2/issue/", json_data=payload)["key"]

    request_fn(
        "POST",
        f"/rest/api/2/issue/{old_key}/comment",
        json_data={
            "body": f"Migrated to [{new_key}]({jira_url}/browse/{new_key}) as a {new_type.upper()}."
        },
    )

    transitions = request_fn("GET", f"/rest/api/2/issue/{old_key}/transitions")[
        "transitions"
    ]
    transition_id = next(
        (
            t["id"]
            for t in transitions
            if t["name"].lower() in ["done", "closed", "cancelled"]
        ),
        None,
    )
    if not transition_id and transitions:
        transition_id = transitions[0]["id"]

    if transition_id:
        request_fn(
            "POST",
            f"/rest/api/2/issue/{old_key}/transitions",
            json_data={"transition": {"id": transition_id}},
        )

    return new_key
