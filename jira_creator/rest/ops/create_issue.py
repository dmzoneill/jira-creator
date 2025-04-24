#!/usr/bin/env python
"""
Creates an issue by sending a POST request using the provided request function.

Args:
request_fn (function): A function that sends HTTP requests. It is expected to accept at least the following
parameters:
- method (str): The HTTP method to use (e.g., "GET", "POST").
- url (str): The URL to send the request to.
- json (dict): A dictionary containing the payload data to be sent in JSON format.
payload (dict): A dictionary representing the data to be sent as the payload for creating the issue.

Returns:
str: The key of the created issue, or an empty string if the key is not found in the response.
"""


def create_issue(request_fn, payload):
    """
    Creates an issue by sending a POST request using the provided request function.

    Args:
    request_fn (function): A function that sends HTTP requests. It is expected to accept at least the following
    parameters:
    - method (str): The HTTP method to use (e.g., "GET", "POST").
    - url (str): The URL to send the request to.
    - json (dict): A dictionary containing the payload data to be sent in JSON format.
    payload (dict): A dictionary representing the data to be sent as the payload for creating the issue.

    Returns:
    str: The key of the created issue, or an empty string if the key is not found in the response.
    """

    return request_fn("POST", "/rest/api/2/issue/", json=payload).get("key", "")
