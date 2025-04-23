"""
This script defines a function 'change_issue_type' that changes the type of a given issue in a Jira instance. It takes
three parameters: 'request_fn' for making HTTP requests, 'issue_key' to identify the issue, and 'new_type' to specify
the new issue type.
It retrieves issue data using the 'request_fn', modifies the type in the payload, and updates the issue type via a PUT
request to the Jira API. If the issue is a subtask, it also handles removing the parent link.
In case of a 'ChangeIssueTypeError', it raises and logs an exception with an error message.
"""

from exceptions.exceptions import ChangeIssueTypeError


def change_issue_type(request_fn, issue_key, new_type):
    """
    Change the issue type of a Jira issue.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - issue_key (str): The key of the issue to be updated.
    - new_type (str): The new issue type to assign to the issue.

    Side Effects:
    - Modifies the issue type of the specified Jira issue.

    Exceptions:
    - None
    """

    try:
        issue_data = request_fn("GET", f"/rest/api/2/issue/{issue_key}")
        is_subtask = issue_data["fields"]["issuetype"]["subtask"]
        payload = {"fields": {"issuetype": {"name": new_type.capitalize()}}}
        if is_subtask:
            payload["update"] = {"parent": [{"remove": {}}]}

        request_fn("PUT", f"/rest/api/2/issue/{issue_key}", json=payload)
    except ChangeIssueTypeError as e:
        msg = f"❌ Failed to change issue type: {e}"
        print(msg)
        raise ChangeIssueTypeError(msg)
