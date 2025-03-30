from unittest.mock import MagicMock

import pytest

from jira_creator.rh_jira import JiraCLI


@pytest.fixture
def cli():
    return JiraCLI()


def test_set_story_points_success(monkeypatch, cli):
    mock_set_story_points = MagicMock()
    cli.jira = MagicMock(set_story_points=mock_set_story_points)

    class Args:
        issue_key = "AAP-12345"
        points = 5

    cli.set_story_points(Args())
    mock_set_story_points.assert_called_once_with("AAP-12345", 5)


def test_set_story_points_failure(monkeypatch, cli, capsys):
    def boom(issue_key, points):
        raise Exception("fake failure")

    cli.jira = MagicMock(set_story_points=boom)

    class Args:
        issue_key = "AAP-12345"
        points = 5

    cli.set_story_points(Args())
    captured = capsys.readouterr()
    assert "❌ Failed to set story points" in captured.out


def test_set_story_points_value_error(capsys):
    cli = JiraCLI()

    class Args:
        issue_key = "AAP-456"
        points = "five"  # invalid non-integer value

    cli.set_story_points(Args())

    captured = capsys.readouterr()
    assert "❌ Points must be an integer." in captured.out
