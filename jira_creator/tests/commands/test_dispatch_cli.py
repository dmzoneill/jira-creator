def test_dispatch_unknown_command(cli):

    class DummyArgs:
        command = "does-not-exist"

    cli._dispatch_command(DummyArgs())  # should print error but not crash
