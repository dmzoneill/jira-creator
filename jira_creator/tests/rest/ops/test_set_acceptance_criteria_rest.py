from core.env_fetcher import EnvFetcher


def test_set_acceptance_criteria(capsys, client):
    issue_key = "AAP-test_set_acceptance_criteria"
    acceptance_criteria = "Acceptance criteria description"

    # Simulate the GET and PUT responses correctly
    client._request.side_effect = [
        {
            "fields": {
                EnvFetcher.get(
                    "JIRA_ACCEPTANCE_CRITERIA_FIELD"
                ): "Acceptance criteria description"
            }
        },  # GET response with 'fields'
        {},  # PUT response (successful)
    ]

    # Call the set_acceptance_criteria method
    client.set_acceptance_criteria(issue_key, acceptance_criteria)

    # Capture the output printed by the function
    captured = capsys.readouterr().out

    # Assert that the output contains the expected success message
    assert f"✅ Updated acceptance criteria of {issue_key}" in captured
