#!/usr/bin/env python
"""
This module contains unit tests for the `blocked` method of the `client` class, which identifies blocked issues in a
system. The tests cover various scenarios, including the presence and absence of blocked issues, cases where no issues
are present, and handling exceptions during issue listing.

The tests utilize `MagicMock` from the `unittest.mock` module to simulate the behavior of the `client` object, enabling
controlled testing environments. The `pytest` framework is used for assertions and exception handling. Additionally,
the `EnvFetcher` class is employed to retrieve environment variables related to JIRA issue fields.
"""

from unittest.mock import MagicMock

import pytest
from core.env_fetcher import EnvFetcher


def test_get_blocked_issues_found(client):
    """
    Retrieve a list of blocked issues found in the system.

    Arguments:
    - client: An object representing the client used to interact with the system.

    Return:
    - This function does not return any value.

    Exceptions:
    - None
    """

    client.list_issues = MagicMock(
        return_value=[
            {
                "key": "AAP-test_get_blocked_issues_found",
                "fields": {
                    "summary": "Fix DB timeout",
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "Alice"},
                    EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": "True"},
                    EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "DB down",
                },
            }
        ]
    )

    result = client.blocked()
    assert len(result) == 1
    assert result[0]["key"] == "AAP-test_get_blocked_issues_found"
    assert result[0]["reason"] == "DB down"


def test_get_blocked_issues_none_blocked(client):
    """
    Retrieve a list of blocked issues from the client, returning an empty list if no issues are blocked.

    Arguments:
    - client: An object representing the client used to interact with the system.

    Return:
    - None

    Side Effects:
    - Modifies the behavior of the client object by mocking the list_issues method.

    Exceptions:
    - None
    """

    client.list_issues = MagicMock(
        return_value=[
            {
                "key": "AAP-test_get_blocked_issues_none_blocked",
                "fields": {
                    "summary": "Write docs",
                    "status": {"name": "To Do"},
                    "assignee": {"displayName": "Bob"},
                    EnvFetcher.get("JIRA_BLOCKED_FIELD"): {"value": "False"},
                    EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"): "",
                },
            }
        ]
    )
    result = client.blocked()
    assert len(result) == 0


def test_get_blocked_issues_no_issues(client):
    """
    This function tests the behavior of the 'blocked' method in the client when there are no blocked issues.

    Arguments:
    - client: An instance of a client object.

    Side Effects:
    - Mocks the 'list_issues' method of the client object to return an empty list.
    """

    client.list_issues = MagicMock(return_value=[])
    result = client.blocked()
    assert result == []


def test_get_blocked_issues_exception(client):
    """
    Simulate an exception when listing blocked issues.

    Arguments:
    - client: An object representing a client connection.

    Exceptions:
    - Exception: Raised when there is a simulated failure in listing blocked issues.
    """

    client.list_issues = MagicMock(side_effect=Exception("Simulated list failure"))

    with pytest.raises(Exception, match="Simulated list failure"):
        client.blocked()
