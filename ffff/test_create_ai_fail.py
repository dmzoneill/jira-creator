from jira_creator.rh_jira import JiraCLI
from unittest.mock import MagicMock
import tempfile
import os


def test_create_ai_failure(capsys):
    cli = JiraCLI()

    # Mocking the methods
    cli.jira.build_payload = MagicMock(return_value={})
    cli.jira.create_issue = MagicMock(return_value="AAP-6")

    # Mock the AI provider to raise an exception
    cli.ai_provider.improve_text = MagicMock(side_effect=Exception("ai fail"))

    # Mocking the NamedTemporaryFile
    with tempfile.NamedTemporaryFile(delete=False, mode="w+") as tf:
        tf.write("template")
        tf.flush()
        tf.seek(0)

    # Set the Args
    class Args:
        type = "story"
        summary = "summary"
        edit = False
        dry_run = True

    # Call the create method
    cli.create(Args())

    # Capture the output
    out = capsys.readouterr().out
    assert "📦 DRY RUN ENABLED" in out

    # Cleanup the temp file after the test
    os.remove(tf.name)
