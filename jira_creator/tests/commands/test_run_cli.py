import os
import sys
from unittest.mock import MagicMock, patch


def test_run(cli):
    cli._dispatch_command = MagicMock()

    def fake_register(subparsers):
        subparsers.add_parser("fake")

    cli._register_subcommands = fake_register

    with (
        patch.object(sys, "argv", ["rh-issue", "fake"]),
        patch.dict(os.environ, {"CLI_NAME": "rh-issue"}),
    ):
        cli.run()

    cli._dispatch_command.assert_called_once()
