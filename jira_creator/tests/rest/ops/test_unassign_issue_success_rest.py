from unittest.mock import MagicMock


def test_unassign_issue(client):
    # Mock the _request method to simulate a successful request
    client._request = MagicMock(return_value={})

    # Call unassign_issue and assert the result
    result = client.unassign_issue("AAP-test_unassign_issue")
    assert result is True
