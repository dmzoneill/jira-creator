#!/usr/bin/env python
"""
This script defines a test function to test the run method of a CLI class using unittest.mock for mocking objects.
The test function sets up a mock for the _dispatch_command method of the provided cli object and asserts its call
during run.
It also includes a fake_register function to add a 'fake' sub-command for testing purposes.
"""

import os
import sys
from unittest.mock import MagicMock, patch


def test_run(cli):
    """
    Set up a mock for the _dispatch_command method of the provided cli object for testing purposes.
    Arguments:
    - cli (object): The cli object for which the _dispatch_command method will be mocked.
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
