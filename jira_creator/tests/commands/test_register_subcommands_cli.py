def test_register_subcommands_does_not_crash(cli):
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
