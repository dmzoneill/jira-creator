from unittest.mock import MagicMock


def test_set_component(client):
    client._request = MagicMock(return_value={})

    client.set_component("AAP-123", "New Component")

    client._request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/AAP-123/components",
        json={"components": [{"name": "New Component"}]},
    )
