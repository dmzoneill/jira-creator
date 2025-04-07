from unittest.mock import MagicMock


def test_remove_from_sprint_error(capsys, client):
    # Mock the _request method to raise an exception
    client._request = MagicMock(side_effect=Exception("fail"))

    # Call the remove_from_sprint method
    client.remove_from_sprint("AAP-test_remove_from_sprint_error")

    # Capture the output and assert the error message
    out = capsys.readouterr().out
    assert "❌ Failed to remove from sprint" in out
