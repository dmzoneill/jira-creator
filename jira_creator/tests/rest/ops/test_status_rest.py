#!/usr/bin/env python
"""
Set the status of the client using a simulated side effect for multiple calls.

Arguments:
- client: An object representing the client to set the status for.

Side Effects:
- Modifies the side effect of the client's request attribute for multiple calls.
"""

import pytest
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import SetStatusError


# /* jscpd:ignore-start */
def test_set_status_success(client):
    """
    Test the success case where the status of the issue is successfully set.
    """
    # Simulate the side effect of the client's request for transitions
    client.request.side_effect = [{"transitions": [{"name": "Done", "id": "2"}]}, {}]

    # Call the method to set the status
    client.set_status("AAP-test_set_status", "Done")

    # Assert that the request was called twice (once for transitions and once for setting the status)
    assert client.request.call_count == 2


def test_set_status_target_status_not_found(client):
    """
    Test the case where the target status is not found in the available transitions.
    """
    # Simulate the side effect of the client's request with no matching target status
    client.request.side_effect = [{"transitions": [{"name": "To Do", "id": "1"}]}, {}]

    # Call the method to set the status to a non-existent target status
    with pytest.raises(SetStatusError):
        client.set_status("AAP-test_set_status", "In Progress")

    # Assert that the request was called twice
    assert client.request.call_count == 1


def test_set_status_refinement_status(client):
    """
    Test the case where the target status is 'refinement' and move the issue to the backlog.
    """
    # Simulate the side effect of the client's request for transitions (with "refinement" status)
    client.request.side_effect = [
        {"transitions": [{"name": "Refinement", "id": "3"}]},
        {"issues": [{"key": "AAP-12345"}]},  # Simulated backlog response
        {"status": "success"},  # Simulate successful rank response
        {
            "fields": {EnvFetcher.get("JIRA_EPIC_FIELD"): "EPIC-5678"},
            "id": "123",
        },  # Simulated issue details response
        {},
        {},
    ]

    # Call the method to set the status to "refinement"
    client.set_status("AAP-test_set_status", "Refinement")

    # Assert that the request was called four times (transitions, backlog, rank, issue details)
    assert client.request.call_count == 6


def test_set_status_refinement_no_backlog(client):
    """
    Test the case where no backlog issues are available when setting the status to 'refinement'.
    """
    # Simulate the side effect of the client's request for transitions (with "refinement" status)
    client.request.side_effect = [
        {"transitions": [{"name": "Refinement", "id": "3"}]},
        {"issues": []},  # Simulated backlog response
        {"status": "success"},  # Simulate successful rank response
        {
            "fields": {EnvFetcher.get("JIRA_EPIC_FIELD"): "EPIC-5678"},
            "id": "123",
        },  # Simulated issue details response
        {},
        {},
    ]

    # Call the method to set the status to "refinement"
    client.set_status("AAP-test_set_status", "Refinement")

    # Assert that the request was called four times (transitions, backlog, rank, issue details)
    assert client.request.call_count == 4


def test_set_status_unexpected_error(client):
    """
    Test the case where an unexpected error occurs during the status change.
    """
    # Simulate the side effect of the client's request with an unexpected error
    client.request.side_effect = RuntimeError("Unexpected error")

    # Call the method to set the status and ensure it raises the appropriate error
    with pytest.raises(RuntimeError):
        client.set_status("AAP-test_set_status", "Done")

    # Assert that the request was called once (transitions request)
    assert client.request.call_count == 1


# /* jscpd:ignore-end */
