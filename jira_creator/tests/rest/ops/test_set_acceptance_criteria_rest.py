from unittest.mock import MagicMock

from rest.client import JiraClient


def test_set_acceptance_criteria(capsys):
    # Create an instance of JiraClient
    client = JiraClient()

    # Mock the _request method
    client._request = MagicMock()

    issue_key = "AAP-100"
    acceptance_criteria = "Acceptance criteria description"

    # Simulate the GET and PUT responses correctly
    client._request.side_effect = [
        {
            "fields": {"customfield_12315940": "Acceptance criteria description"}
        },  # GET response with 'fields'
        {},  # PUT response (successful)
    ]

    # Call the set_acceptance_criteria method
    client.set_acceptance_criteria(issue_key, acceptance_criteria)

    # Capture the output printed by the function
    captured = capsys.readouterr().out

    # Assert that the output contains the expected success message
    assert f"✅ Updated acceptance criteria of {issue_key}" in captured
