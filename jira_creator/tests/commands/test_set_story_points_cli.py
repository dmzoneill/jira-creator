from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import SetStoryPointsError


def test_set_story_points_success(cli):
    mock_set_story_points = MagicMock()
    cli.jira = MagicMock(set_story_points=mock_set_story_points)

    class Args:
        issue_key = "AAP-test_set_story_points_success"
        points = 5

    cli.set_story_points(Args())
    mock_set_story_points.assert_called_once_with(
        "AAP-test_set_story_points_success", 5
    )


def test_set_story_points_failure(cli, capsys):
    def boom(issue_key, points):
        raise SetStoryPointsError("fake failure")

    cli.jira = MagicMock(set_story_points=boom)

    class Args:
        issue_key = "AAP-test_set_story_points_failure"
        points = 5

    with pytest.raises(SetStoryPointsError):
        cli.set_story_points(Args())

    captured = capsys.readouterr()
    assert "❌ Failed to set story points" in captured.out


def test_set_story_points_value_error(cli, capsys):
    class Args:
        issue_key = "AAP-test_set_story_points_value_error"
        points = "five"  # invalid non-integer value

    cli.set_story_points(Args())

    captured = capsys.readouterr()
    assert "❌ Points must be an integer." in captured.out
