#!/usr/bin/env python
"""
This file contains unit test functions for testing the methods set_sprint and remove_from_sprint of a client object.
The tests use MagicMock to mock the _request method of the client object and assert the expected behavior of the
methods. The set_sprint method is expected to make a PUT request with specific parameters, while the remove_from_sprint
method is expected to make a POST request with specific parameters.

Functions:
- test_set_sprint(client): Set an empty dictionary as the return value for the _request method of the provided client.
- test_remove_from_sprint(client): Set the _request attribute of the client object to a MagicMock instance that returns
an empty dictionary.
"""

from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_set_sprint(client):
    """
    Set an empty dictionary as the return value for the _request method of the provided client.

    Arguments:
    - client: An object representing a client.

    Side Effects:
    - Modifies the return value of the _request method of the client object.
    """

    client.request = MagicMock(return_value={})

    client.set_sprint("AAP-test_set_sprint", 42)

    client.request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/AAP-test_set_sprint",
        json_data={"fields": {EnvFetcher.get("JIRA_SPRINT_FIELD"): ["42"]}},
    )


def test_remove_from_sprint(client):
    """
    Set the _request attribute of the client object to a MagicMock instance that returns an empty dictionary.
    """

    client.request = MagicMock(return_value={})

    client.remove_from_sprint("AAP-test_remove_from_sprint")

    client.request.assert_called_once_with(
        "POST",
        "/rest/agile/1.0/backlog/issue",
        json_data={
            "issues": ["AAP-test_remove_from_sprint"]
        },  # Matching the actual call
    )
