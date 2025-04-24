#!/usr/bin/env python
"""
This script defines a function 'migrate_issue' that facilitates migrating an issue in Jira from one type to another.
The function takes several parameters including request_fn for making HTTP requests, jira_url for the Jira instance URL,
build_payload_fn for constructing the payload for the new issue, old_key for the key of the issue to be migrated, and
new_type for the type of the new issue.

The function retrieves information about the old issue, creates a new issue with the specified type, and updates the old
issue with a comment indicating the migration. It also transitions the old issue to a final state if possible.

The function returns the key of the newly created issue.
"""


def migrate_issue(request_fn, jira_url, build_payload_fn, old_key, new_type):
    """
    Retrieve issue details from Jira and prepare data for migration.

    Arguments:
    - request_fn (function): A function to make HTTP requests.
    - jira_url (str): The base URL of the Jira instance.
    - build_payload_fn (function): A function to construct payload for HTTP requests.
    - old_key (str): The key of the issue to be migrated.
    - new_type (str): The type of the new issue after migration.

    Returns:
    This function does not return any value.
    """

    fields = request_fn("GET", f"/rest/api/2/issue/{old_key}")["fields"]
    summary = fields.get("summary", f"Migrated from {old_key}")
    description = fields.get("description", f"Migrated from {old_key}")

    payload = build_payload_fn(summary, description, new_type)
    new_key = request_fn("POST", "/rest/api/2/issue/", json=payload)["key"]

    request_fn(
        "POST",
        f"/rest/api/2/issue/{old_key}/comment",
        json={
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
            json={"transition": {"id": transition_id}},
        )

    return new_key
