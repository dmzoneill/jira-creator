#!/usr/bin/env python
"""
Defines a function to set the priority of an issue identified by the given issue key.

Functions:
- set_priority(request_fn: Callable[[str, str, dict], None], issue_key: str, priority: str) -> None:
Set the priority of an issue identified by the given issue key.

Arguments:
- request_fn (Callable[[str, str, dict], None]): The function used to make the request.
- issue_key (str): The unique key identifying the issue.
- priority (str): The priority level to set for the issue. Should be one of: "critical", "major", "normal", or "minor".
"""
from typing import Callable


def set_priority(
    request_fn: Callable[[str, str, dict], None], issue_key: str, priority: str
) -> None:
    """
    Set the priority of an issue identified by the given issue key.

    Arguments:
    - request_fn (Callable[[str, str, dict], None]): The function used to make the request.
    - issue_key (str): The unique key identifying the issue.
    - priority (str): The priority level to set for the issue. Should be one of: "critical", "major", "normal", or
    "minor".
    """

    priorities: dict[str, str] = {
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
        json_data={"fields": {"priority": {"name": priority}}},
    )
