#!/usr/bin/env python
"""
This script defines a test function to validate the response handling of the OpenAIProvider class. It mocks a response
object with a status code of 200 and a JSON payload containing a message with content "✓". The function then replaces
the requests.post method with a lambda function that returns the mock response. It creates an instance of the
OpenAIProvider class, calls the improve_text method with dummy arguments, and asserts that the result is equal to "✓".

The test_openai_response_handling function handles the response from OpenAI API after requesting text improvement. It
modifies the behavior of the requests.post function to return a mock response. The function takes no arguments and
returns the improved text as a string. No exceptions are raised during the execution of this function.
"""

import requests
from providers.openai_provider import OpenAIProvider


def test_openai_response_handling():
    """
    Handles the response from OpenAI API after requesting text improvement.

    Arguments:
    - No arguments.

    Return:
    - The improved text as a string.

    Exceptions:
    - No exceptions raised.

    Side Effects:
    - Modifies the behavior of the requests.post function to return a mock response.
    """

    mock = type(
        "Response",
        (),
        {
            "status_code": 200,
            "json": lambda self: {"choices": [{"message": {"content": "✓"}}]},
        },
    )
    requests.post = lambda *a, **kw: mock()
    provider = OpenAIProvider()
    result = provider.improve_text("prompt", "dirty text")
    assert result == "✓"
