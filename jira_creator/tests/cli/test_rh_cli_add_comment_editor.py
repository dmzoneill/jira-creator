import os
from jira_creator.rh_jira import JiraCLI
import tempfile
from unittest.mock import MagicMock


def test_add_comment_editor():
    cli = JiraCLI()

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
        issue_key = "AAP-1"
        text = tf.name  # Use the file path for the comment

    # Call the add_comment method
    cli.add_comment(Args())

    # Clean up the temporary file
    os.remove(tf.name)

    # Ensure the add_comment method was called
    cli.jira.add_comment.assert_called_once_with("AAP-1", "my comment")
