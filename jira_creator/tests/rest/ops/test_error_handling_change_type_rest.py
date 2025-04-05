from unittest.mock import MagicMock


def test_change_issue_type_fails(client):

    # Mock the _request method to raise an exception
    client._request = MagicMock(side_effect=Exception("failure"))

    # Attempt to change the issue type
    success = client.change_issue_type("AAP-1", "task")

    # Assert that the operation failed
    assert not success
