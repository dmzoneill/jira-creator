def test_vote_story_points_value_error(cli, capsys):
    class Args:
        issue_key = "AAP-test_vote_story_points_value_error"
        points = "notanint"

    cli.vote_story_points(Args())
    out = capsys.readouterr().out
    assert "❌ Points must be an integer." in out
