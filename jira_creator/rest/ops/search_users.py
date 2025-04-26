#!/usr/bin/env python
"""
Search for users based on a query string.

Arguments:
- request_fn (Callable[..., Any]): A function used to make HTTP requests.
- query (str): The query string used to search for users by username.
- max_results (int): The maximum number of results to return (default is 10).

Return:
- List[Dict[str, Any]]: A list of user objects matching the search query.
"""

from typing import Any, Callable, Dict, List


def search_users(
    request_fn: Callable[..., Any], query: str, max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for users based on a query string.

    Arguments:
    - request_fn (Callable[..., Any]): A function used to make HTTP requests.
    - query (str): The query string used to search for users by username.
    - max_results (int): The maximum number of results to return (default is 10).

    Return:
    - List[Dict[str, Any]]: A list of user objects matching the search query.
    """

    return request_fn(
        "GET",
        "/rest/api/2/user/search",
        params={"username": query, "maxResults": max_results},
    )
