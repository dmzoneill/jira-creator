def test_assign_issue_failure(capfd, client):
    # Simulate a failure by raising an exception
    def mock_request_fail(*args, **kwargs):
        raise Exception("kaboom")

    client._request = mock_request_fail

    result = client.assign_issue("AAP-test_assign_issue_failure", {"name": "johndoe"})
    out = capfd.readouterr().out

    assert result is False
    assert "❌ Failed to assign issue AAP-test_assign_issue_failure" in out
