from unittest.mock import MagicMock


def test_set_story_epic_rest(client):
    client._request = MagicMock(return_value={})

    # Call the function to set story points
    client.set_story_epic("AAP-123", "AAP-456")

    # Assert that the PUT request is called with the correct payload and endpoint
    client._request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/AAP-123",
        json={"fields": {"customfield_12311140": "AAP-456"}},
    )
