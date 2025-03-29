from unittest.mock import MagicMock, patch
from rh_jira import JiraCLI


def test_edit_prompt_fallback(monkeypatch):
    cli = JiraCLI()
    monkeypatch.setattr(cli.jira, "get_description", lambda k: "")
    monkeypatch.setattr(
        cli.jira, "get_issue_type", lambda k: (_ for _ in ()).throw(Exception("fail"))
    )
    monkeypatch.setattr(cli.jira, "update_description", lambda k, v: None)
    monkeypatch.setattr("subprocess.call", lambda cmd: 0)

    class DummyTempFile:
        def __init__(self):
            self.name = "temp.md"

        def write(self, content):
            pass

        def flush(self):
            pass

        def seek(self, n):
            pass

        def read(self):
            return "edited"

    monkeypatch.setattr("tempfile.NamedTemporaryFile", lambda *a, **kw: DummyTempFile())

    class Args:
        issue_key = "AAP-1"
        no_ai = True

    cli.edit_issue(Args())


def test_edit_issue_prompt_fallback(monkeypatch):
    cli = JiraCLI()
    cli.jira = MagicMock()
    cli.default_prompt = "fallback prompt"

    # Set up mocks
    cli.jira.get_description.return_value = "original text"
    cli.jira.get_issue_type.return_value = "unknown"

    args = MagicMock()
    args.issue_key = "JIRA-123"

    # Mock editor interaction
    monkeypatch.setenv("EDITOR", "true")  # prevent actual editor from launching
    monkeypatch.setattr("tempfile.NamedTemporaryFile", MagicMock())
    mock_tempfile = cli.edit_issue.__globals__[
        "tempfile"
    ].NamedTemporaryFile.return_value.__enter__.return_value
    mock_tempfile.name = "/fake/file.md"
    mock_tempfile.read.return_value = "edited content"

    # Simulate prompt failure
    with patch("rh_jira.JiraPromptLibrary.get_prompt", side_effect=Exception("💥")):
        cli.edit_issue(args)

    # Check that fallback prompt was used
    assert cli.default_prompt == "fallback prompt"
