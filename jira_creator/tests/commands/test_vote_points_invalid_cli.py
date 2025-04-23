def test_vote_story_points_value_error(cli, capsys):
    """
    This function is used to test a specific scenario where a ValueError is raised when attempting to vote for story
    points. It takes two arguments:
    1. cli: An instance of the command-line interface.
    2. capsys: A pytest fixture to capture stdout and stderr output.

    The function creates an inner class Args with two attributes:
    - issue_key: A string representing the key of the issue being voted on.
    - points: A string representing the points to be voted on, which intentionally contains a non-integer value.

    This function is designed to test the behavior of the system when a non-integer value is provided for story points
    during a voting process.
    """

    class Args:
        issue_key = "AAP-test_vote_story_points_value_error"
        points = "notanint"

    cli.vote_story_points(Args())
    out = capsys.readouterr().out
    assert "❌ Points must be an integer." in out
