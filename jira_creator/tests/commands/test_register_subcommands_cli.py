#!/usr/bin/env python
"""
This script defines a function test_register_subcommands_does_not_crash(cli) that tests the _register_subcommands
method of a CLI class. It creates a dummy parser object using lambda functions to simulate the behavior of the
add_parser and add_argument methods. The test function is designed to ensure that the _register_subcommands method does
not crash when called with the dummy parser object.

Function test_register_subcommands_does_not_crash(cli):
- Register subcommands for the CLI without crashing.
- Arguments:
- cli: An instance of the CLI class.
- Side Effects:
- Modifies the subcommands of the CLI instance by registering them using the provided parser.
"""


def test_register_subcommands_does_not_crash(cli):
    """
    Register subcommands for the CLI without crashing.

    Arguments:
    - cli: An instance of the CLI class.

    Side Effects:
    - Modifies the subcommands of the CLI instance by registering them using the provided parser.
    """

    parser = type(
        "DummySubparsers",
        (),
        {
            "add_parser": lambda *a, **kw: type(
                "DummyArgParser", (), {"add_argument": lambda *a, **kw: None}
            )()
        },
    )()
    cli._register_subcommands(parser)
