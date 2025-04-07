from unittest.mock import MagicMock


def test_vote_story_points(cli, capsys):
    cli.jira.vote_story_points = MagicMock()

    class Args:
        issue_key = "AAP-test_vote_story_points"
        points = "8"

    cli.vote_story_points(Args())
    cli.jira.vote_story_points.assert_called_once_with("AAP-test_vote_story_points", 8)
    out = capsys.readouterr().out
    assert "✅ Voted" in out
