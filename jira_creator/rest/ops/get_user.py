#!/usr/bin/env python
"""
Retrieves user information by sending a GET request to the specified API endpoint.

Arguments:
- request_fn (Callable[[str, str], dict]): A function used to make HTTP requests.
- username (str): The username of the user whose information is being retrieved.

Return:
- dict: A dictionary containing the user information retrieved from the API.
"""


from typing import Callable


def get_user(request_fn: Callable[[str, str], dict], username: str) -> dict:
    """
    Retrieves user information by sending a GET request to the specified API endpoint.

    Arguments:
    - request_fn (Callable[[str, str], dict]): A function used to make HTTP requests.
    - username (str): The username of the user whose information is being retrieved.

    Return:
    - dict: A dictionary containing the user information retrieved from the API.
    """

    return request_fn("GET", "/rest/api/2/user", params={"username": username})
