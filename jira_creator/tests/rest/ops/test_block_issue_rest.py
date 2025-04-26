#!/usr/bin/env python
"""
This file contains a unit test to validate that the block_issue method of the client class is calling the expected
fields with the correct payload. The test uses a MagicMock object to mock the _request method of the client and checks
if it is called once with the appropriate arguments. The payload is constructed using values fetched from the
EnvFetcher class.

Tested Function:
test_block_issue_calls_expected_fields(client)
- Summary: Mocks the client's request method and calls the block_issue method with specified parameters.
- Arguments:
- client (object): The client object used to interact with an external service.
- Return: This function does not return any value.
- Exceptions: This function does not raise any exceptions.
"""

from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_block_issue_calls_expected_fields(client):
    """
    Summary:
    Mocks the client's request method and calls the block_issue method with specified parameters.

    Arguments:
    - client (object): The client object used to interact with an external service.

    Return:
    This function does not return any value.

    Exceptions:
    This function does not raise any exceptions.
    """

    client.request = MagicMock()
    client.block_issue("ABC-123", "Waiting for dependency")

    payload = {}
    payload[EnvFetcher.get("JIRA_BLOCKED_FIELD")] = {"value": True}
    payload[EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD")] = "Waiting for dependency"

    client.request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/ABC-123",
        json_data=payload,
    )
