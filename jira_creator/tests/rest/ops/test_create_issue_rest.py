from unittest.mock import MagicMock


def test_create_issue(client):
    """
    Creates an issue using the provided client.

    Arguments:
    - client: An object representing the client used to interact with an issue tracking system.

    Side Effects:
    - Modifies the client's _request method to return a response with a 'key' attribute.
    """

    # Mock the _request method to return a response with a 'key'
    client._request = MagicMock(return_value={"key": "AAP-test_create_issue"})

    # Call create_issue and assert that the returned key matches the mocked value
    key = client.create_issue({"fields": {"summary": "Test"}})
    assert key == "AAP-test_create_issue"
