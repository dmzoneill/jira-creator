#!/usr/bin/env python3
import importlib
import inspect
import os
import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction
from pathlib import Path


class InspectJiraCLI:
    def __init__(self) -> None:
        pass

    def run(self) -> None:
        import argcomplete

        InspectJiraCLI_prog_name: str = os.environ.get(
            "CLI_NAME", os.path.basename(sys.argv[0])
        )
        InspectJiraCLI_parser: ArgumentParser = ArgumentParser(
            description="JIRA Issue Tool", prog=InspectJiraCLI_prog_name
        )
        subparsers: _SubParsersAction = InspectJiraCLI_parser.add_subparsers(
            dest="command", required=True
        )

        self._register_subcommands(subparsers)
        argcomplete.autocomplete(InspectJiraCLI_parser)

        args: Namespace = InspectJiraCLI_parser.parse_args()
        self._dispatch_command(args)

    def _register_subcommands(self, subparsers: _SubParsersAction) -> None:

        # Dynamically load all command modules and call their register_commands function
        command_dir = "commands"

        # Iterate through each Python file in the 'commands' directory
        for filename in os.listdir(command_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                command_name = filename[:-3]  # Strip off the '.py' extension
                module = importlib.import_module(f"commands.{command_name}")
                if hasattr(module, "register_commands"):
                    # Call the register_commands function from the module
                    module.register_commands(subparsers)

                    # Get all functions in the module
                    functions = inspect.getmembers(module, inspect.isfunction)

                    # Loop through the functions and add them to the object's scope
                    for name, func in functions:
                        # Add function as an attribute to the JiraCLI instance
                        setattr(self, name, func)

        return

    def _dispatch_command(self, args: Namespace) -> None:
        try:
            getattr(self, "cli_" + args.command.replace("-", "_"))(self.jira, args)
        except AttributeError as e:
            msg: str = f"❌ Command failed: {e}"
            print(msg)
            raise Exception(msg)


if __name__ == "__main__":  # pragma: no cover
    JiraCLI().run()  # pragma: no cover
