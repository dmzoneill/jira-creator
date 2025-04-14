from unittest.mock import MagicMock


def test_list_sprints(client):
    request_mock = MagicMock(return_value={"sprints": ["Sprint 1", "Sprint 2"]})
    client._request = request_mock
    board_id = "dummy_board_id"

    response = client.list_sprints(board_id)

    assert response == ["Sprint 1", "Sprint 2"]
    client._request.assert_called_once_with(
        "GET", "/rest/api/2/board/dummy_board_id/sprint"
    )
