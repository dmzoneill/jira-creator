import tempfile
from unittest.mock import MagicMock


def test_create_editor(cli):
    # Mocking the methods
    cli.jira.create_issue = MagicMock(return_value="AAP-test_create_editor")
    cli.ai_provider.improve_text = MagicMock(return_value="description")

    # Create a temporary file and write the description into it
    with tempfile.NamedTemporaryFile(delete=False, mode="w+") as tf:
        tf.write("description")
        tf.flush()
        tf.seek(0)

    # Set the Args for the CLI command
    class Args:
        type = "story"
        summary = "My Summary"
        edit = True
        dry_run = False

    # Call the create method
    cli.create_issue(Args())

    # Cleanup the temp file after the test
    # os.remove(tf.name)
