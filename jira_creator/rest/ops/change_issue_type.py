#!/usr/bin/env python
"""
This script defines a function 'change_issue_type' that changes the type of a given issue in a Jira instance. It takes
three parameters: 'request_fn' for making HTTP requests, 'issue_key' to identify the issue, and 'new_type' to specify
the new issue type.
It retrieves issue data using the 'request_fn', modifies the type in the payload, and updates the issue type via a PUT
request to the Jira API. If the issue is a subtask, it also handles removing the parent link.
In case of a 'ChangeIssueTypeError', it raises and logs an exception with an error message.

Function 'change_issue_type':
- Arguments:
- request_fn (function): A function used to make HTTP requests.
- issue_key (str): The key of the issue to be updated.
- new_type (str): The new issue type to assign to the issue.
- Side Effects:
- Modifies the issue type of the specified Jira issue.
- Exceptions:
- ChangeIssueTypeError: Raised if there is an issue with changing the issue type.
"""

from typing import Any, Callable, Dict

from exceptions.exceptions import ChangeIssueTypeError


def change_issue_type(
    request_fn: Callable[[str, str, Dict[str, Any]], None],
    issue_key: str,
    new_type: str,
) -> None:
    """
    Change the issue type of a Jira issue.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the issue to be updated.
    - new_type (str): The new issue type to assign to the issue.

    Side Effects:
    - Modifies the issue type of the specified Jira issue.

    Exceptions:
    - ChangeIssueTypeError: Raised if there is an issue with changing the issue type.
    """

    try:
        issue_data: Dict[str, Any] = request_fn("GET", f"/rest/api/2/issue/{issue_key}")
        is_subtask: bool = issue_data["fields"]["issuetype"]["subtask"]
        payload: Dict[str, Any] = {
            "fields": {"issuetype": {"name": new_type.capitalize()}}
        }
        if is_subtask:
            payload["update"] = {"parent": [{"remove": {}}]}

        request_fn("PUT", f"/rest/api/2/issue/{issue_key}", json_data=payload)
    except ChangeIssueTypeError as e:
        msg: str = f"❌ Failed to change issue type: {e}"
        print(msg)
        raise ChangeIssueTypeError(e) from e
