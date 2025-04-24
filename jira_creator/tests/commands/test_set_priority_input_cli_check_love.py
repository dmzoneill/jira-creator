#!/usr/bin/env python
"""
This script defines a test function 'test_set_priority_love_input' that tests the 'set_priority' method of a CLI class.
The test creates a MagicMock object and a custom Args class with issue key and priority attributes. It then captures
the output of the method using StringIO and sys.stdout redirection. Finally, it asserts that the output contains a
specific message confirming the priority setting.

Function:
- test_set_priority_love_input(cli): Set the Jira priority for the 'love' input in the CLI.

Arguments:
- cli: An instance of the CLI object.

Side Effects:
- Modifies the 'jira' attribute of the CLI object by assigning a MagicMock object to it.
"""

import sys
from io import StringIO
from unittest.mock import MagicMock


def test_set_priority_love_input(cli):
    """
    Set the Jira priority for the 'love' input in the CLI.

    Arguments:
    - cli: An instance of the CLI object.

    Side Effects:
    - Modifies the 'jira' attribute of the CLI object by assigning a MagicMock object to it.
    """

    cli.jira = MagicMock()

    class Args:
        issue_key = "AAP-test_set_priority_love_input"
        priority = "me love you long time"

    captured_output = StringIO()
    sys.stdout = captured_output

    cli.set_priority(Args())

    sys.stdout = sys.__stdout__
    out = captured_output.getvalue()

    assert "✅ Priority set to 'me love you long time'" in out
