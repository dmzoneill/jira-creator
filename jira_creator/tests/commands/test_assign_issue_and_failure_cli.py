def test_assign_success(cli, capsys):
    cli.jira.assign_issue = lambda k, a: True

    class Args:
        issue_key = "AAP-test_assign_success"
        assignee = "johndoe"

    cli.assign(Args())
    out = capsys.readouterr().out
    assert "✅ assigned AAP-test_assign_success to johndoe" in out


def test_assign_failure(cli, capsys):
    cli.jira.assign_issue = lambda k, a: False

    class Args:
        issue_key = "AAP-test_assign_failure"
        assignee = "johndoe"

    cli.assign(Args())
    out = capsys.readouterr().out
    assert "❌ Could not assign AAP-test_assign_failure to johndoe" in out
