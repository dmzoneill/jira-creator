def test_main_guard():
    """
    This function imports the '__main__' module and assigns it to the variable 'main_script'.
    """

    import __main__ as main_script

    assert hasattr(main_script, "__name__")
