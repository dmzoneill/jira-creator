import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from jira_creator.rh_jira import JiraCLI


def test_run():
    # Mocking the _register_subcommands and _dispatch_command methods
    cli = JiraCLI()
    cli._register_subcommands = MagicMock()
    cli._dispatch_command = MagicMock()

    # Mock argparse.ArgumentParser
    with patch("argparse.ArgumentParser") as MockArgumentParser:
        mock_parser = MagicMock()
        MockArgumentParser.return_value = mock_parser

        # Simulate a successful parse_args call with the expected arguments
        mock_parser.parse_args.return_value = type("Args", (), {"command": "create"})

        # Set the environment variable CLI_NAME (optional)
        with patch.dict(os.environ, {"CLI_NAME": "TestCLI"}):
            cli.run()

        # Check if the _register_subcommands and _dispatch_command were called
        cli._register_subcommands.assert_called_once()
        cli._dispatch_command.assert_called_once_with(
            mock_parser.parse_args.return_value
        )

        # Verify the correct arguments passed to ArgumentParser
        mock_parser.add_subparsers.assert_called_once_with(
            dest="command", required=True
        )
        mock_parser.parse_args.assert_called_once()
