#!/usr/bin/env python
"""
This script contains a unit test function 'test_get_sprint' to test the 'get_sprint' method of a client class.
The test function uses the 'unittest.mock' module to create a MagicMock object for the 'request' method of the client.
It then sets the return value for the MagicMock object and calls the 'get_sprint' method of the client.
The test asserts that the 'request' method was called once with specific arguments and that the response matches the
expected value.
"""
from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher


# /* jscpd:ignore-start */
def test_get_sprint(client):
    client.request = MagicMock(
        return_value={
            "maxResults": 50,
            "startAt": 0,
            "isLast": True,
            "values": [
                {
                    "id": 71828,
                    "self": "https://issues.redhat.com/rest/agile/1.0/sprint/71828",
                    "state": "active",
                    "name": "Cloud Analytics Sprint 2025-17",
                    "startDate": "2025-04-24T12:01:00.000Z",
                    "endDate": "2025-05-01T12:01:00.000Z",
                    "activatedDate": "2025-04-24T14:23:02.844Z",
                    "originBoardId": 21125,
                    "goal": "",
                    "synced": False,
                    "autoStartStop": False,
                }
            ],
        }
    )

    response = client.get_sprint()

    boardNumber = EnvFetcher.get("JIRA_BOARD_ID")
    path = f"/rest/agile/1.0/board/{boardNumber}/sprint?state=active"

    client.request.assert_called_once_with("GET", path)
    assert response == {
        "maxResults": 50,
        "startAt": 0,
        "isLast": True,
        "values": [
            {
                "id": 71828,
                "self": "https://issues.redhat.com/rest/agile/1.0/sprint/71828",
                "state": "active",
                "name": "Cloud Analytics Sprint 2025-17",
                "startDate": "2025-04-24T12:01:00.000Z",
                "endDate": "2025-05-01T12:01:00.000Z",
                "activatedDate": "2025-04-24T14:23:02.844Z",
                "originBoardId": 21125,
                "goal": "",
                "synced": False,
                "autoStartStop": False,
            }
        ],
    }


# /* jscpd:ignore-end */
