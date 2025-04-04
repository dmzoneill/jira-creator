from unittest.mock import MagicMock

from rest.client import JiraClient


def test_get_acceptance_criteria():
    client = JiraClient()

    # Mock _request method to simulate getting description
    client._request = MagicMock(
        return_value={"fields": {"customfield_12315940": "text"}}
    )

    # Call get_description and assert it returns the correct description
    desc = client.get_acceptance_criteria("AAP-1")
    assert desc == "text"
