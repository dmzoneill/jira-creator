"""
This module provides a function to set the status of an issue in a Jira system using the provided request function.

Functions:
- set_status(request_fn, issue_key, target_status): Sets the status of the given issue to the provided target status by
making API calls using the request function.

Raises:
- SetStatusError: Custom exception raised when the target status is not found in the valid transitions for the issue.

Note:
- The request function should be capable of making HTTP requests to the Jira API.
"""

from exceptions.exceptions import SetStatusError


def set_status(request_fn, issue_key, target_status):
    """
    Retrieve the available transitions for a given issue and set its status to a target status.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key identifying the issue to update.
    - target_status (str): The desired status to set for the issue.

    Returns:
    This function does not return anything.

    """

    transitions = request_fn("GET", f"/rest/api/2/issue/{issue_key}/transitions").get(
        "transitions", []
    )

    transition_id = next(
        (t["id"] for t in transitions if t["name"].lower() == target_status.lower()),
        None,
    )

    if not transition_id:
        print("Valid Transitions:")
        for t in transitions:
            print(t["name"])
        raise SetStatusError(f"❌ Transition to status '{target_status}' not found")

    request_fn(
        "POST",
        f"/rest/api/2/issue/{issue_key}/transitions",
        json={"transition": {"id": transition_id}},
    )
    print(f"✅ Changed status of {issue_key} to '{target_status}'")
