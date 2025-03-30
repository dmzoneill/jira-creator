from unittest.mock import MagicMock, patch

from jira.client import JiraClient

from jira_creator.rh_jira import JiraCLI


def test_change_issue_type():
    client = JiraClient()

    # Mock the request method
    mock_request = MagicMock()
    # First call: GET request to fetch issue details
    mock_request.side_effect = lambda method, path, **kwargs: (
        {"fields": {"issuetype": {"subtask": True}}} if method == "GET" else {}
    )

    # Assign the mocked _request method to the client
    client._request = mock_request

    # Call the method
    client.change_issue_type("AAP-1", "story")

    # Assert that the GET request was called to retrieve the issue
    mock_request.assert_any_call("GET", "/rest/api/2/issue/AAP-1")

    # Assert that the PUT request was called to change the issue type
    mock_request.assert_any_call(
        "PUT",
        "/rest/api/2/issue/AAP-1",
        json={
            "fields": {"issuetype": {"name": "Story"}},
            "update": {"parent": [{"remove": {}}]},
        },
        allow_204=True,
    )


def test_change_type_else_block():
    # Create an instance of JiraCLI
    cli = JiraCLI()

    # Mocking Args for issue_key and new_type
    class Args:
        issue_key = "FAKE-123"
        new_type = "bug"

    # Mock the JiraClient's change_issue_type to return False to hit the else block
    with patch.object(cli.jira, "change_issue_type", return_value=False):
        # Mocking the print function to capture the output
        with patch("builtins.print") as mock_print:
            # Call the change_type method
            cli.change_type(Args())

            # Ensure that print was called with the correct "❌ Change failed" message
            mock_print.assert_called_with("❌ Change failed for FAKE-123")
