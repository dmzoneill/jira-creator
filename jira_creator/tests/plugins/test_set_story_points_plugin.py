#!/usr/bin/env python
"""Tests for the set story points plugin."""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.plugins.set_story_points_plugin import SetStoryPointsPlugin


class TestSetStoryPointsPlugin:
    """Test cases for SetStoryPointsPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = SetStoryPointsPlugin()
        assert plugin.command_name == "set-story-points"
        assert plugin.help_text == "Set the story points of a Jira issue"
        assert plugin.field_name == "story points"
        assert plugin.argument_name == "points"
        assert plugin.argument_help == "The story points value (integer)"

    def test_register_arguments(self):
        """Test argument registration, including integer validation for points."""
        plugin = SetStoryPointsPlugin()
        parser = ArgumentParser()
        plugin.register_arguments(parser)

        args = parser.parse_args(["PROJ-123", "5"])
        assert args.issue_key == "PROJ-123"
        assert args.points == 5

        with pytest.raises(SystemExit):
            parser.parse_args(["PROJ-123", "not-a-number"])

    def test_argument_type_is_int(self):
        """Story points are registered as integers."""
        plugin = SetStoryPointsPlugin()
        assert plugin.argument_type is int

    @patch("jira_creator.plugins.set_story_points_plugin.EnvFetcher")
    def test_rest_operation(self, mock_env_fetcher):
        """Test the REST operation directly."""
        plugin = SetStoryPointsPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        # Mock EnvFetcher.get to return story points field
        mock_env_fetcher.get.return_value = "customfield_10004"

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", value=5)

        # Verify EnvFetcher was called
        mock_env_fetcher.get.assert_called_once_with("JIRA_STORY_POINTS_FIELD")

        # Verify the request
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10004": 5}},
        )
        assert result == {"key": "TEST-123"}

    @patch("jira_creator.plugins.set_story_points_plugin.EnvFetcher")
    def test_execute_success(self, mock_env_fetcher, capsys):
        """Test successful execution."""
        plugin = SetStoryPointsPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        # Mock EnvFetcher.get to return story points field
        mock_env_fetcher.get.return_value = "customfield_10004"

        args = Namespace(issue_key="TEST-123", points=8)

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10004": 8}},
        )

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Story points for TEST-123 set to '8'" in captured.out

    @patch("jira_creator.plugins.set_story_points_plugin.EnvFetcher")
    def test_execute_with_zero_points(self, mock_env_fetcher, capsys):
        """Test execution with zero story points (clearing)."""
        plugin = SetStoryPointsPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        mock_env_fetcher.get.return_value = "customfield_10004"

        args = Namespace(issue_key="TEST-123", points=0)

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10004": 0}},
        )

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Story points for TEST-123 set to '0'" in captured.out

    @patch("jira_creator.plugins.set_story_points_plugin.EnvFetcher")
    def test_execute_failure(self, mock_env_fetcher, capsys):
        """Test execution with API failure."""
        plugin = SetStoryPointsPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = Exception("Invalid story points value")

        mock_env_fetcher.get.return_value = "customfield_10004"

        args = Namespace(issue_key="TEST-123", points=100)

        # Verify exception is raised
        with pytest.raises(Exception) as exc_info:
            plugin.execute(mock_client, args)

        # Verify the exception message contains the error
        assert "Invalid story points value" in str(exc_info.value)

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to set story points:" in captured.out

    @patch("jira_creator.plugins.set_story_points_plugin.EnvFetcher")
    def test_execute_with_different_points(self, mock_env_fetcher):
        """Test execute with different story point values."""
        plugin = SetStoryPointsPlugin()
        mock_client = Mock()
        mock_env_fetcher.get.return_value = "customfield_10004"

        # Common Fibonacci sequence values used for story points
        test_points = [1, 2, 3, 5, 8, 13, 21]

        for points in test_points:
            mock_client.reset_mock()
            args = Namespace(issue_key="TEST-123", points=points)

            result = plugin.execute(mock_client, args)

            assert result is True
            # Verify the points value was passed correctly
            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["fields"]["customfield_10004"] == points

    @patch("jira_creator.plugins.set_story_points_plugin.EnvFetcher")
    def test_rest_operation_with_negative_points(self, mock_env_fetcher):
        """Test REST operation with negative story points."""
        plugin = SetStoryPointsPlugin()
        mock_client = Mock()
        mock_env_fetcher.get.return_value = "customfield_10004"

        # Negative points might be invalid in Jira, but the plugin should still send them
        plugin.rest_operation(mock_client, issue_key="TEST-456", value=-5)

        # Verify the negative value is passed through
        call_args = mock_client.request.call_args[1]["json_data"]
        assert call_args["fields"]["customfield_10004"] == -5

    @patch("jira_creator.plugins.set_story_points_plugin.EnvFetcher")
    def test_rest_operation_with_large_points(self, mock_env_fetcher):
        """Test REST operation with large story point values."""
        plugin = SetStoryPointsPlugin()
        mock_client = Mock()
        mock_env_fetcher.get.return_value = "customfield_10004"

        # Test with a large value
        large_value = 999999
        plugin.rest_operation(mock_client, issue_key="TEST-789", value=large_value)

        # Verify the large value is passed through
        call_args = mock_client.request.call_args[1]["json_data"]
        assert call_args["fields"]["customfield_10004"] == large_value

    @patch("jira_creator.plugins.set_story_points_plugin.EnvFetcher")
    def test_env_fetcher_returns_different_field(self, mock_env_fetcher):
        """Test that the plugin uses the field returned by EnvFetcher."""
        plugin = SetStoryPointsPlugin()
        mock_client = Mock()

        # Test with different custom field IDs
        custom_fields = ["customfield_10001", "customfield_20002", "story_points_field"]

        for field_id in custom_fields:
            mock_client.reset_mock()
            mock_env_fetcher.get.return_value = field_id

            plugin.rest_operation(mock_client, issue_key="TEST-123", value=5)

            # Verify the correct field ID was used
            call_args = mock_client.request.call_args[1]["json_data"]
            assert field_id in call_args["fields"]
            assert call_args["fields"][field_id] == 5
