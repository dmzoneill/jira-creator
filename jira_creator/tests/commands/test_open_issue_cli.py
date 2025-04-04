import subprocess
from unittest.mock import MagicMock, patch

from jira_creator.rh_jira import JiraCLI


def test_open_issue():
    # Patch os.getenv to return a mock JIRA URL
    with patch("os.getenv", return_value="https://your-jira-url.com"):
        # Patch subprocess.Popen to prevent actually opening a process
        with patch("subprocess.Popen") as mock_popen:
            cli = JiraCLI()

            class Args:
                issue_key = "AAP-1"

            # Simulate subprocess.Popen succeeding
            mock_popen.return_value = True

            # Call the method
            cli.open_issue(Args())

            # Assert that subprocess.Popen was called with the correct arguments
            mock_popen.assert_called_once_with(
                ["xdg-open", "https://your-jira-url.com/browse/AAP-1"]
            )


def test_open_issue_exception_handling():
    # Patch os.getenv to return a mock JIRA URL
    with patch("os.getenv", return_value="https://your-jira-url.com"):
        # Patch subprocess.Popen to simulate an exception
        with patch("subprocess.Popen") as mock_popen:
            cli = JiraCLI()

            class Args:
                issue_key = "AAP-1"

            # Simulate subprocess.Popen raising an exception
            mock_popen.side_effect = subprocess.SubprocessError("Failed to open issue")

            # Call the method
            with patch(
                "builtins.print"
            ) as mock_print:  # Mock print to check the output
                cli.open_issue(Args())

                # Assert that print was called with the correct error message
                mock_print.assert_called_once_with(
                    "❌ Failed to open issue AAP-1: Failed to open issue"
                )
