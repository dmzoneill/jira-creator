#!/usr/bin/env python
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
