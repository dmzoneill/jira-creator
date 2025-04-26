#!/usr/bin/env python
"""
This module provides functionality to retrieve a list of open sprints for a specified board using an HTTP request.

The primary function in this module is `list_sprints`, which retrieves the names of open sprints associated with a
given board.

Functions:
- list_sprints(request_fn, board_id: str) -> list[str]:
Retrieves the names of open sprints associated with the specified board.

Parameters:
- request_fn: A callable function that performs HTTP requests.
- board_id (str): The identifier of the board for which to retrieve the sprints.

Returns:
- A list of strings containing the names of open sprints.

Exceptions:
- This function does not raise any exceptions.
"""


def list_sprints(request_fn, board_id: str) -> list[str]:
    """
    Retrieve a list of open sprints for a specified board.

    Arguments:
    - request_fn: A function used to make HTTP requests.
    - board_id (str): The identifier of the board for which to retrieve the sprints.

    Return:
    - list[str]: A list of names of open sprints associated with the specified board.

    Exceptions:
    - This function does not raise any exceptions.
    """

    path = f"/rest/agile/1.0/board/{board_id}/sprint"
    res = request_fn("GET", path)
    sprints = res.get("values")
    open_sprints = [sprint["name"] for sprint in sprints if sprint["state"] != "closed"]
    return open_sprints
