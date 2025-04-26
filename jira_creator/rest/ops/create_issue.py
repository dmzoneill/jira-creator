#!/usr/bin/env python
"""
This script defines a function create_issue that sends a POST request to create an issue using the provided request
function and payload data.

Parameters:
- request_fn: A callable that takes a method (str), endpoint (str), and data (Dict) as arguments and returns a Dict
response.
- payload: A Dict containing data to be sent in the request.

Returns:
- A string representing the key of the created issue.
"""
from typing import Callable, Dict


def create_issue(request_fn: Callable[[str, str, Dict], Dict], payload: Dict) -> str:
    """
    Creates an issue by sending a POST request to the specified API endpoint with the provided payload data.

    Arguments:
    - request_fn (Callable): A function that sends HTTP requests. It takes three arguments: method (str), endpoint
    (str), and data (Dict). Used to make a POST request to create the issue.
    - payload (Dict): A dictionary containing data for creating the issue.

    Return:
    - str: The key of the created issue, extracted from the response data. Returns an empty string if the key is not
    found in the response.

    """
    return request_fn("POST", "/rest/api/2/issue/", json_data=payload).get("key", "")
