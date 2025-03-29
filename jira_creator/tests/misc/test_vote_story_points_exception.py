from jira_creator.rh_jira import JiraCLI


def test_vote_story_points_error(monkeypatch, capsys):
    cli = JiraCLI()
    cli.jira.vote_story_points = lambda k, v: (_ for _ in ()).throw(Exception("fail"))

    class Args:
        issue_key = "AAP-2"
        points = "8"

    cli.vote_story_points(Args())
    out = capsys.readouterr().out
    assert "❌ Failed to vote on story points" in out
