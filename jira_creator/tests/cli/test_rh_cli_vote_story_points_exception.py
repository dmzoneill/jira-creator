from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_vote_story_points_error(capsys):
    cli = JiraCLI()

    # Mock the vote_story_points method to simulate an error
    cli.jira.vote_story_points = MagicMock(side_effect=Exception("fail"))

    class Args:
        issue_key = "AAP-2"
        points = "8"

    # Call the method and capture the output
    cli.vote_story_points(Args())
    out = capsys.readouterr().out

    # Assert that the error message is in the output
    assert "❌ Failed to vote on story points" in out
