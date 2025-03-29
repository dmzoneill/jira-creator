from rh_jira import JiraCLI


def test_set_status_print(monkeypatch):
    cli = JiraCLI()
    monkeypatch.setattr(cli.jira, "set_status", lambda k, s: None)

    class Args:
        issue_key = "AAP-1"
        status = "Done"

    cli.set_status(Args())
