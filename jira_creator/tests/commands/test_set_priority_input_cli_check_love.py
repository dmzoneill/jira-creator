import sys
from io import StringIO
from unittest.mock import MagicMock


def test_set_priority_love_input(cli):
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
