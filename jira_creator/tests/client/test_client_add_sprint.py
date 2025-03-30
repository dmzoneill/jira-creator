from unittest.mock import MagicMock

import pytest
from jira.client import JiraClient


def test_add_to_sprint_by_name_success():
    # Create the JiraClient instance
    client = JiraClient()

    # Mock the _request method to simulate sprint lookup and assignment
    client._request = MagicMock(
        side_effect=[
            {"values": [{"id": 88, "name": "Sprint 42"}]},  # Sprint lookup
            {},  # Assignment
        ]
    )

    # Call the add_to_sprint_by_name method
    client.add_to_sprint_by_name("AAP-1", "Sprint 42")

    # Assert that _request was called twice
    assert client._request.call_count == 2


def test_add_to_sprint_by_name_not_found():
    # Create the JiraClient instance
    client = JiraClient()

    # Mock the _request method to simulate sprint lookup where the sprint is not found
    client._request = MagicMock(return_value={"values": []})

    # Try to add the issue to a non-existent sprint and check for the exception
    with pytest.raises(Exception) as exc:
        client.add_to_sprint_by_name("AAP-1", "Nonexistent Sprint")

    # Assert that the exception message contains 'Could not find sprint'
    assert "Could not find sprint" in str(exc.value)
