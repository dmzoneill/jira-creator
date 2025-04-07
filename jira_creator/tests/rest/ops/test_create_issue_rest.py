from unittest.mock import MagicMock


def test_create_issue(client):
    # Mock the _request method to return a response with a 'key'
    client._request = MagicMock(return_value={"key": "AAP-test_create_issue"})

    # Call create_issue and assert that the returned key matches the mocked value
    key = client.create_issue({"fields": {"summary": "Test"}})
    assert key == "AAP-test_create_issue"
