from unittest.mock import MagicMock


def test_get_issue_type(client):
    # Mock the _request method to simulate a successful response
    client._request = MagicMock(
        return_value={"fields": {"issuetype": {"name": "Story"}}}
    )

    # Call the get_issue_type method with a sample issue key
    result = client.get_issue_type("AAP-test_get_issue_type")

    # Check if the result is the correct issue type
    assert result == "Story"
    # Ensure that _request was called with the expected arguments
    client._request.assert_called_once_with(
        "GET", "/rest/api/2/issue/AAP-test_get_issue_type"
    )
