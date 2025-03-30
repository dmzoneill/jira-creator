from unittest.mock import MagicMock
from jira_creator.rh_jira import JiraCLI


def test_run_register_dispatch():
    cli = JiraCLI()

    # Mock the _register_subcommands and _dispatch_command methods
    cli._register_subcommands = MagicMock()
    cli._dispatch_command = MagicMock()

    # Create a dummy parser class to mock add_subparsers and parse_args methods
    class DummyParser:
        def __init__(self):
            self.commands = {}

        def add_subparsers(self, *args, **kwargs):
            return self

        def parse_args(self):
            # Returning a valid command here (e.g., "create")
            return type("Args", (), {"command": "create"})

    # Mock argparse.ArgumentParser to use the DummyParser
    cli._parser = MagicMock()
    cli._parser.add_subparsers = MagicMock(return_value=DummyParser())
    cli._parser.parse_args = MagicMock(
        return_value=type("Args", (), {"command": "create"})
    )

    # Run the CLI
    cli.run()
