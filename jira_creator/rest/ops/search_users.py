#!/usr/bin/env python
"""
Search for users based on a query string.

Arguments:
- request_fn (function): A function used to make HTTP requests.
- query (str): The query string used to search for users by username.
- max_results (int): The maximum number of results to return (default is 10).

Return:
- list: A list of user objects matching the search query.
"""


def search_users(request_fn, query: str, max_results: int = 10) -> list:
    """
    Search for users based on a query string.

    Arguments:
    - request_fn (function): A function used to make HTTP requests.
    - query (str): The query string used to search for users by username.
    - max_results (int): The maximum number of results to return (default is 10).

    Return:
    - list: A list of user objects matching the search query.
    """

    return request_fn(
        "GET",
        "/rest/api/2/user/search",
        params={"username": query, "maxResults": max_results},
    )
