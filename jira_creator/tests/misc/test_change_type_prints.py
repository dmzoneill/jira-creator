from jira_creator.rh_jira import JiraCLI


def test_change_type_prints(monkeypatch):
    cli = JiraCLI()

    monkeypatch.setattr(cli.jira, "change_issue_type", lambda k, t: True)

    class Args:
        issue_key = "AAP-123"
        new_type = "story"

    cli.change_type(Args())

    monkeypatch.setattr(cli.jira, "change_issue_type", lambda k, t: False)
    cli.change_type(Args())
