#!/usr/bin/env python
"""
This script defines a function test_main_guard() that imports the '__main__' module and assigns it to the variable
'main_script'. It then asserts that the 'main_script' variable has the attribute "__name__".
"""

"""
This function imports the '__main__' module and assigns it to the variable 'main_script'.
"""


def test_main_guard():
    """
    This function imports the '__main__' module and assigns it to the variable 'main_script'.
    """

    import __main__ as main_script

    assert hasattr(main_script, "__name__")
