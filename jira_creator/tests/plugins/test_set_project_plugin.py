#!/usr/bin/env python
"""Tests for the set project plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import SetProjectError
from jira_creator.plugins.set_project_plugin import SetProjectPlugin


class TestSetProjectPlugin:
    """Test cases for SetProjectPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = SetProjectPlugin()
        assert plugin.command_name == "set-project"
        assert plugin.help_text == "Set the project of a Jira issue"
        assert plugin.field_name == "project"
        assert plugin.argument_name == "project"
        assert plugin.argument_help == "The project key to move the issue to"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = SetProjectPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        # Verify add_argument was called with correct parameters
        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list

        # First argument: issue_key
        assert calls[0][0] == ("issue_key",)
        assert calls[0][1]["help"] == "The Jira issue key (e.g., PROJ-123)"

        # Second argument: project
        assert calls[1][0] == ("project",)
        assert calls[1][1]["help"] == "The project key to move the issue to"

    def test_rest_operation(self):
        """Test the REST operation directly."""
        plugin = SetProjectPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "NEWPROJ-123"}

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", value="NEWPROJ")

        # Verify the request
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"project": {"key": "NEWPROJ"}}},
        )
        assert result == {"key": "NEWPROJ-123"}

    def test_execute_success(self, capsys):
        """Test successful execution."""
        plugin = SetProjectPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "PROJ2-123"}

        args = Namespace(issue_key="PROJ1-123", project="PROJ2")

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/PROJ1-123",
            json_data={"fields": {"project": {"key": "PROJ2"}}},
        )

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Project for PROJ1-123 set to 'PROJ2'" in captured.out

    def test_execute_failure(self, capsys):
        """Test execution with API failure."""
        plugin = SetProjectPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = SetProjectError("Project not found")

        args = Namespace(issue_key="TEST-123", project="INVALID")

        # Verify exception is raised
        with pytest.raises(SetProjectError) as exc_info:
            plugin.execute(mock_client, args)

        # Verify the exception message
        assert str(exc_info.value) == "Project not found"

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to set project: Project not found" in captured.out

    def test_execute_with_different_projects(self):
        """Test execute with different project keys."""
        plugin = SetProjectPlugin()
        mock_client = Mock()

        test_projects = ["PROJ1", "PROJ2", "DEV", "PROD", "TEST"]

        for project in test_projects:
            mock_client.reset_mock()
            args = Namespace(issue_key="OLD-123", project=project)

            result = plugin.execute(mock_client, args)

            assert result is True
            # Verify the project was passed correctly
            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["fields"]["project"]["key"] == project

    def test_rest_operation_with_different_formats(self):
        """Test REST operation with different project key formats."""
        plugin = SetProjectPlugin()
        mock_client = Mock()

        project_keys = [
            "ABC",
            "ABCD",
            "ABC123",
            "A1B2",
            "LONGPROJECT",
        ]

        for project_key in project_keys:
            mock_client.reset_mock()

            plugin.rest_operation(mock_client, issue_key="TEST-456", value=project_key)

            # Verify project key is preserved
            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["fields"]["project"]["key"] == project_key

    def test_execute_with_permission_error(self, capsys):
        """Test execution when user lacks permission to move issue."""
        plugin = SetProjectPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = SetProjectError("You do not have permission to move issues to this project")

        args = Namespace(issue_key="TEST-123", project="RESTRICTED")

        with pytest.raises(SetProjectError) as exc_info:
            plugin.execute(mock_client, args)

        assert "You do not have permission" in str(exc_info.value)

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to set project:" in captured.out
        assert "You do not have permission" in captured.out
