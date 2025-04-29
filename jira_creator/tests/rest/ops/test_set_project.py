from unittest.mock import MagicMock


def test_set_project(client):
    client._request = MagicMock(return_value={})

    client.set_project("PROJ-123", "NEWPROJ")

    client._request.assert_called_once_with(
        "PUT",
        "/rest/api/2/issue/PROJ-123",
        json={"fields": {"project": {"key": "NEWPROJ"}}},
    )
