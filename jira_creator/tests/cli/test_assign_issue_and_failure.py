from jira_creator.rh_jira import JiraCLI


def test_assign_success(capsys):
    cli = JiraCLI()
    cli.jira.assign_issue = lambda k, a: True

    class Args:
        issue_key = "AAP-123"
        assignee = "johndoe"

    cli.assign(Args())
    out = capsys.readouterr().out
    assert "✅ assigned AAP-123 to johndoe" in out


def test_assign_failure(capsys):
    cli = JiraCLI()
    cli.jira.assign_issue = lambda k, a: False

    class Args:
        issue_key = "AAP-123"
        assignee = "johndoe"

    cli.assign(Args())
    out = capsys.readouterr().out
    assert "❌ Could not assign AAP-123 to johndoe" in out
