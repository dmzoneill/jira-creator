#!/usr/bin/env python
"""
This module defines a function 'remove_from_sprint' that is used to remove an issue from a sprint in an Agile project
management tool. It takes two parameters: 'request_fn' which is a function for making HTTP requests and 'issue_key'
which is the key of the issue to be removed from the sprint. If the issue is successfully removed from the sprint, a
success message is printed. If an error occurs during the removal process, a failure message is printed and a
'RemoveFromSprintError' exception is raised with an error message.

The 'remove_from_sprint' function removes an issue from the current sprint backlog. It takes 'request_fn' as a function
used to make HTTP requests and 'issue_key' as the key of the issue to be removed. It may raise a 'RemoveFromSprintError'
exception if there is an issue removing the specified issue from the sprint backlog. Upon successful removal, it prints
a message indicating that the issue has been moved to the backlog. If an error occurs, it prints a failure message and
raises a 'RemoveFromSprintError' exception.
"""

from exceptions.exceptions import RemoveFromSprintError


def remove_from_sprint(request_fn, issue_key):
    """
    Removes an issue from the current sprint backlog.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the issue to be removed from the sprint backlog.

    Exceptions:
    - RemoveFromSprintError: Raised when there is an issue removing the specified issue from the sprint backlog.

    Side Effects:
    - If successful, prints a message indicating that the issue has been moved to the backlog.
    - If an error occurs, prints a message indicating the failure and raises a RemoveFromSprintError.
    """

    try:
        request_fn(
            "POST",
            "/rest/agile/1.0/backlog/issue",
            json={"issues": [issue_key]},
        )
        print(f"✅ Moved {issue_key} to backlog")
    except RemoveFromSprintError as e:
        msg = f"❌ Failed to remove from sprint: {e}"
        print(msg)
        raise RemoveFromSprintError(e) from e
