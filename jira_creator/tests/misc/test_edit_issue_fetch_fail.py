from jira_creator.rh_jira import JiraCLI


def test_edit_issue_fetch_fail(monkeypatch):
    cli = JiraCLI()
    monkeypatch.setattr(
        cli.jira, "get_description", lambda k: (_ for _ in ()).throw(Exception("fail"))
    )

    class Args:
        issue_key = "AAP-1"
        no_ai = False

    cli.edit_issue(Args())
