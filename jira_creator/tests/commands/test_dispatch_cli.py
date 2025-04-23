import pytest
from exceptions.exceptions import DispatcherError


def test_dispatch_unknown_command(cli):
    """
    Dispatches an unknown command for testing purposes.

    Arguments:
    - cli (object): An object representing the command line interface.

    This function is used to test the behavior of dispatching an unknown command in a command line interface.
    """

    class DummyArgs:
        command = "does-not-exist"

    with pytest.raises(DispatcherError):
        cli._dispatch_command(DummyArgs())  # should print error but not crash
