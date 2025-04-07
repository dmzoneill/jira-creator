from unittest.mock import MagicMock


def test_unassign_issue_fails(capsys, client):
    # Mock the _request method to simulate an exception
    client._request = MagicMock(side_effect=Exception("fail"))

    # Call unassign_issue and assert the result
    result = client.unassign_issue("AAP-test_unassign_issue_fails")
    assert not result

    # Check that the error message was captured in the output
    out = capsys.readouterr().out
    assert "❌ Failed to unassign issue" in out
