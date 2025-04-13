from unittest.mock import patch

import pytest
from exceptions.exceptions import OpenIssueError


def test_open_issue(cli):
    # Patch subprocess.Popen to prevent actually opening a process
    with patch("subprocess.Popen") as mock_popen:

        class Args:
            issue_key = "AAP-test_open_issue"

        # Simulate subprocess.Popen succeeding
        mock_popen.return_value = True

        # Call the method
        cli.open_issue(Args())

        # Assert that subprocess.Popen was called with the correct arguments
        mock_popen.assert_called_once_with(
            ["xdg-open", "https://example.atlassian.net/browse/AAP-test_open_issue"]
        )


def test_open_issue_exception_handling(cli):
    # Patch subprocess.Popen to simulate an exception
    with patch("subprocess.Popen") as mock_popen:

        class Args:
            issue_key = "AAP-test_open_issue_exception_handling"

        # Simulate subprocess.Popen raising an exception
        mock_popen.side_effect = OpenIssueError("Failed to open issue")

        # Call the method
        with patch("builtins.print") as mock_print:  # Mock print to check the output
            with pytest.raises(OpenIssueError):
                cli.open_issue(Args())

            # Assert that print was called with the correct error message
            mock_print.assert_called_once_with(
                "❌ Failed to open issue AAP-test_open_issue_exception_handling: Failed to open issue"
            )
