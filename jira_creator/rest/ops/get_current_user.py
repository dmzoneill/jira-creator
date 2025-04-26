#!/usr/bin/env python
"""
Retrieve the current user's name or account ID.

Arguments:
- request_fn (function): A function used to make a request to an API endpoint.

Return:
- str: The name of the current user if available, otherwise the account ID.
"""


from typing import Any, Callable, Dict


def get_current_user(request_fn: Callable[[str, str], Dict[str, Any]]) -> str:
    """
    Retrieve the current user's name or account ID.

    Arguments:
    - request_fn (Callable[[str, str], Dict[str, Any]]): A function used to make a request to an API endpoint.

    Return:
    - str: The name of the current user if available, otherwise the account ID.
    """

    user: Dict[str, Any] = request_fn("GET", "/rest/api/2/myself")
    return user.get("name") or user.get("accountId")
