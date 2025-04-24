#!/usr/bin/env python
"""
This script defines a test case for the 'test_create_editor' function. It mocks the 'create_issue' and 'improve_text'
methods using MagicMock. It creates a temporary file, writes a description into it, sets arguments for the CLI command,
and calls the 'create_issue' method with the provided arguments. After the test, it cleans up the temporary file.
"""

import tempfile
from unittest.mock import MagicMock


def test_create_editor(cli):
    """
    Mock methods related to creating an editor in a testing environment.

    Arguments:
    - cli: A testing CLI object that allows mocking methods for creating an editor.

    Side Effects:
    - Mocks the 'create_issue' method of the Jira client to return a test value.
    - Mocks the 'improve_text' method of the AI provider to return a test value.
    """

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
