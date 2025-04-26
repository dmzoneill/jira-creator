#!/usr/bin/env python
"""
This file contains a unit test for the 'get_sprint' function in the CLI module. It mocks the 'get_sprint' method of the
Jira class to return a success status. The test captures the output and asserts that the word 'success' is present in
the output. It also checks if the 'get_sprint' method was called once with no arguments.
"""
from unittest.mock import MagicMock


def test_cli_get_sprint_success(cli, capsys):
    # Mock the add_flag_to_issue method of jira
    cli.jira.get_sprint = MagicMock(
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

    class Args:
        pass

    cli.get_sprint(Args())

    # Capture output and assert
    out = capsys.readouterr().out
    assert "Cloud Analytics Sprint 2025-17" in out
    cli.jira.get_sprint.assert_called_once_with()
