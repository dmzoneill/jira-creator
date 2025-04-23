"""
This script defines a test function to test the run method of a CLI class. It uses unittest.mock to create a MagicMock
object and patch the sys.argv and os.environ for testing purposes. The test function sets up a fake subcommand and
asserts that the dispatch_command method is called once during the run.
"""

import os
import sys
from unittest.mock import MagicMock, patch


def test_run(cli):
    """
    Set up a mock for the _dispatch_command method of the provided cli object for testing purposes.
    """

    cli._dispatch_command = MagicMock()

    def fake_register(subparsers):
        """
        Adds a sub-command 'fake' to the provided subparsers object.

        Arguments:
        - subparsers (argparse.ArgumentParser): An ArgumentParser object to which the 'fake' sub-command will be added.

        Side Effects:
        Modifies the subparsers object by adding a new sub-command 'fake'.
        """

        subparsers.add_parser("fake")

    cli._register_subcommands = fake_register

    with (
        patch.object(sys, "argv", ["rh-issue", "fake"]),
        patch.dict(os.environ, {"CLI_NAME": "rh-issue"}),
    ):
        cli.run()

    cli._dispatch_command.assert_called_once()
