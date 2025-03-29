from rh_jira import JiraCLI


def test_try_cleanup_error(monkeypatch, capsys):
    cli = JiraCLI()
    cli.ai_provider.improve_text = lambda p, t: (_ for _ in ()).throw(Exception("fail"))
    result = cli._try_cleanup("prompt", "text")
    assert result == "text"
