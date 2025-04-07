from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


def test_get_acceptance_criteria(client):
    # Mock _request method to simulate getting description
    client._request = MagicMock(
        return_value={
            "fields": {EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD"): "text"}
        }
    )

    # Call get_description and assert it returns the correct description
    desc = client.get_acceptance_criteria("AAP-test_get_acceptance_criteria")
    assert desc == "text"
