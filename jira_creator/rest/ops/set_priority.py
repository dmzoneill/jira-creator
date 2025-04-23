"""
A function to set the priority of an issue in a Jira system.

:param request_fn: Function to send HTTP requests.
:param issue_key: Key of the issue to update.
:param priority: Priority level to set for the issue (critical, major, normal, minor).
"""


def set_priority(request_fn, issue_key, priority):
    """
    Set the priority of an issue identified by the given issue key.

    Arguments:
    - request_fn (function): The function used to make the request.
    - issue_key (str): The unique key identifying the issue.
    - priority (str): The priority level to set for the issue. Should be one of: "critical", "major", "normal", or
    "minor".

    """

    # Put this somewhere else
    priorities = {
        "critical": "Critical",
        "major": "Major",
        "normal": "Normal",
        "minor": "Minor",
    }

    priority = (
        priorities[priority.lower()] if priority.lower() in priorities else "Normal"
    )

    request_fn(
        "PUT",
        f"/rest/api/2/issue/{issue_key}",
        json={"fields": {"priority": {"name": priority}}},
    )
