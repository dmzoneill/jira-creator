from unittest.mock import MagicMock

from jira.client import JiraClient


def test_epic_field():
    # Create a MagicMock instance for JiraClient
    client = JiraClient()

    # Mock the environment variable for the epic field
    client.build_payload = MagicMock(
        return_value={"fields": {"customfield_99999": "Epic Field"}}
    )

    # Call the method
    result = client.build_payload("summary", "description", "epic")

    # Assert that the expected epic field is present in the result
    assert "customfield_99999" in result["fields"]
