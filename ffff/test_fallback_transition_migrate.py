from unittest.mock import MagicMock
from jira.client import JiraClient

def test_migrate_fallback_transition():
    client = JiraClient()

    # Mock the _request method to simulate various API responses
    client._request = MagicMock(side_effect=lambda method, path, **kwargs: {
        "/rest/api/2/issue/AAP-1": {
            "fields": {"summary": "Old summary", "description": "Old desc"},
            "key": "AAP-1",
        },
        "/rest/api/2/issue/": {
            "key": "AAP-2",
        },
        "/comment": {},
        "/transitions": {
            "transitions": [{"id": "5", "name": "Some Status"}]  # Make sure 'transitions' is in the mock response
        }
    }.get(path, {}))  # Return an empty dictionary for other paths

    client.jira_url = "http://fake"

    # Call the migrate_issue method
    new_key = client.migrate_issue("AAP-1", "story")

    # Assert that the issue key has been successfully migrated
    assert new_key == "AAP-2"

    # Assert the correct number of API calls were made (GET issue, POST create issue, POST comment, GET transitions)
    assert client._request.call_count == 4
