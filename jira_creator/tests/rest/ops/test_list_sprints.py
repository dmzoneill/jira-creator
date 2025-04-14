from unittest.mock import MagicMock


def test_list_sprints(client):
    values = {
        "values": [
            {"name": "Sprint 1", "state": "open"},
            {"name": "Sprint 2", "state": "open"},
        ]
    }
    request_mock = MagicMock(return_value=values)
    client._request = request_mock
    board_id = "dummy_board_id"

    response = client.list_sprints(board_id)

    assert response == ["Sprint 1", "Sprint 2"]
