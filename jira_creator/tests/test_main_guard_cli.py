def test_main_guard():
    import __main__ as main_script

    assert hasattr(main_script, "__name__")
