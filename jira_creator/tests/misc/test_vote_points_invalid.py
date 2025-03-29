from jira_creator.rh_jira import JiraCLI


def test_vote_story_points_value_error(capsys):
    cli = JiraCLI()

    class Args:
        issue_key = "AAP-123"
        points = "notanint"

    cli.vote_story_points(Args())
    out = capsys.readouterr().out
    assert "❌ Points must be an integer." in out
