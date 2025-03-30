from unittest.mock import MagicMock

from jira.client import JiraClient


def test_get_update_description():
    client = JiraClient()

    # Mock _request method to simulate getting description
    client._request = MagicMock(return_value={"fields": {"description": "text"}})

    # Call get_description and assert it returns the correct description
    desc = client.get_description("AAP-1")
    assert desc == "text"

    # Create a dictionary to capture the updated fields
    updated = {}

    # Mock _request method to simulate updating description
    client._request = MagicMock(
        side_effect=lambda *a, **k: updated.update(k.get("json", {}))
    )

    # Call update_description and assert that the description field is updated
    client.update_description("AAP-1", "new text")
    assert "description" in updated["fields"]
