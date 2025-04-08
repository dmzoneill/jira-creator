import tempfile
from unittest.mock import MagicMock, patch

import pytest
from exceptions.exceptions import AiError


def test_add_comment_editor(cli):
    # Mock the add_comment method and the improve_text method
    cli.jira.add_comment = MagicMock()
    cli.ai_provider.improve_text = MagicMock(return_value="my comment")

    # Create a temporary file and write to it
    tf = tempfile.NamedTemporaryFile(delete=False, mode="w+")
    tf.write("my comment")
    tf.flush()
    tf.seek(0)

    # Use the temporary file as input for the comment
    class Args:
        issue_key = "AAP-test_add_comment_editor"
        text = tf.name  # Use the file path for the comment

    # Call the add_comment method
    cli.add_comment(Args())

    # Clean up the temporary file
    # os.remove(tf.name)

    # Ensure the add_comment method was called
    cli.jira.add_comment.assert_called_once_with(
        "AAP-test_add_comment_editor", "my comment"
    )


def test_add_comment_with_editor_and_ai_exception_handling(cli, capsys):
    # Mock the AI provider's improve_text method to avoid calling the real AI service
    cli.ai_provider = MagicMock()
    cli.ai_provider.improve_text.side_effect = AiError("AI service failed")

    # Mock the add_comment method (to skip actual Jira interaction)
    cli.jira.add_comment = MagicMock()

    # Mock subprocess.call to avoid opening an editor
    with patch("subprocess.call") as mock_subprocess:
        # Mock TemplateLoader to avoid file access and slow processing
        with patch("builtins.input", return_value="test_input"):
            # Mock the tempfile.NamedTemporaryFile method to simulate file creation and reading
            with patch("tempfile.NamedTemporaryFile") as mock_tempfile:
                mock_tempfile.return_value.__enter__.return_value.write = MagicMock()
                mock_tempfile.return_value.__enter__.return_value.flush = MagicMock()
                mock_tempfile.return_value.__enter__.return_value.read = MagicMock(
                    return_value="Mocked comment"
                )

                # Create an empty text argument to trigger the else block
                class Args:
                    issue_key = (
                        "AAP-test_add_comment_with_editor_and_ai_exception_handling"
                    )
                    text = (
                        ""  # Empty text should trigger the else block (temporary file)
                    )

                with pytest.raises(AiError):
                    # Call the add_comment method
                    cli.add_comment(Args())

                # Capture the printed output
                captured = capsys.readouterr()

                # Check if the subprocess call was made (indicating editor use)
                mock_subprocess.assert_called_once()

                # Assert the expected output (you can check if the process was handled correctly)
                assert "AI service failed" in captured.out
