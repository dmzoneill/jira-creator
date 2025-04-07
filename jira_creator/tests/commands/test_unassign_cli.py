def test_unassign_success(cli, capsys):
    cli.jira.unassign_issue = lambda k: True

    class Args:
        issue_key = "AAP-test_unassign_success"

    cli.unassign(Args())
    out = capsys.readouterr().out
    assert "✅" in out


def test_unassign_failure(cli, capsys):
    cli.jira.unassign_issue = lambda k: False

    class Args:
        issue_key = "AAP-test_unassign_failure"

    cli.unassign(Args())
    out = capsys.readouterr().out
    assert "❌" in out
