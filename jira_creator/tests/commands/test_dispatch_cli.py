import pytest
from exceptions.exceptions import DispatcherError


def test_dispatch_unknown_command(cli):
    class DummyArgs:
        command = "does-not-exist"

    with pytest.raises(DispatcherError):
        cli._dispatch_command(DummyArgs())  # should print error but not crash
