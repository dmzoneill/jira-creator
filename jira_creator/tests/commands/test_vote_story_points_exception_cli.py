from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import VoteStoryPointsError


def test_vote_story_points_error(cli, capsys):
    # Mock the vote_story_points method to simulate an error
    cli.jira.vote_story_points = MagicMock(side_effect=VoteStoryPointsError("fail"))

    class Args:
        issue_key = "AAP-test_vote_story_points_error"
        points = "8"

    with pytest.raises(VoteStoryPointsError):
        # Call the method and capture the output
        cli.vote_story_points(Args())
    out = capsys.readouterr().out

    # Assert that the error message is in the output
    assert "❌ Failed to vote on story points" in out
