from rh_jira import JiraCLI


def test_migrate_success_print(monkeypatch):
    cli = JiraCLI()

    monkeypatch.setattr(cli.jira, "migrate_issue", lambda k, t: "AAP-999")
    monkeypatch.setattr(cli.jira, "jira_url", "http://fake")

    class Args:
        issue_key = "AAP-123"
        new_type = "story"

    cli.migrate(Args())
