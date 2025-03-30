from jira_creator.rh_jira import JiraCLI
from unittest.mock import MagicMock


def test_vote_story_points(monkeypatch, capsys):
    cli = JiraCLI()
    cli.jira.vote_story_points = MagicMock()

    class Args:
        issue_key = "AAP-101"
        points = "8"

    cli.vote_story_points(Args())
    cli.jira.vote_story_points.assert_called_once_with("AAP-101", 8)
    out = capsys.readouterr().out
    assert "✅ Voted" in out