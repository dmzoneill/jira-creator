from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import ChangeIssueTypeError


def test_change_issue_type_fails(client, capsys):
    # Mock the _request method to raise an exception
    client._request = MagicMock(side_effect=ChangeIssueTypeError("failure"))

    with pytest.raises(ChangeIssueTypeError):
        # Attempt to change the issue type
        client.change_issue_type("AAP-test_change_issue_type_fails", "task")

    # Capture the output
    out = capsys.readouterr().out

    # Assert that the correct output was printed
    assert "❌ Failed to change issue type:" in out
