#!/usr/bin/env python
"""Tests for the migrate plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import MigrateError
from jira_creator.plugins.migrate_plugin import MigratePlugin


class TestMigratePlugin:
    """Test cases for MigratePlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = MigratePlugin()
        assert plugin.command_name == "migrate"
        assert plugin.help_text == "Migrate issue to a new type"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = MigratePlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        # Verify arguments were added
        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list
        assert calls[0][0][0] == "issue_key"
        assert calls[0][1]["help"] == "The Jira issue id/key"
        assert calls[1][0][0] == "new_type"
        assert calls[1][1]["help"] == "New issue type"

    def test_rest_operation_success(self):
        """Test successful REST operation for issue migration."""
        plugin = MigratePlugin()
        mock_client = Mock()

        # Set up client attributes
        mock_client.project_key = "TEST"
        mock_client.priority = "Normal"
        mock_client.component_name = "Backend"
        mock_client.affects_version = "1.0"
        mock_client.epic_field = "customfield_10000"
        mock_client.jira_url = "https://jira.example.com"

        # Mock API responses
        mock_client.request.side_effect = [
            # GET old issue
            {
                "fields": {
                    "summary": "Original Summary",
                    "description": "Original Description",
                }
            },
            # POST create new issue
            {"key": "TEST-456"},
            # POST add comment
            {},
            # GET transitions
            {
                "transitions": [
                    {"id": "1", "name": "To Do"},
                    {"id": "2", "name": "Done"},
                ]
            },
            # POST transition
            {},
        ]

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", new_type="bug")

        assert result == {"new_key": "TEST-456"}
        assert mock_client.request.call_count == 5

        # Verify create issue payload
        create_call = mock_client.request.call_args_list[1]
        assert create_call[0][0] == "POST"
        assert create_call[0][1] == "/rest/api/2/issue/"
        payload = create_call[1]["json_data"]["fields"]
        assert payload["summary"] == "Original Summary"
        assert payload["description"] == "Original Description"
        assert payload["issuetype"]["name"] == "Bug"
        assert payload["versions"] == [{"name": "1.0"}]

    def test_rest_operation_epic_type(self):
        """Test REST operation when migrating to epic type."""
        plugin = MigratePlugin()
        mock_client = Mock()

        # Set up client attributes
        mock_client.project_key = "TEST"
        mock_client.priority = "Normal"
        mock_client.component_name = "Backend"
        mock_client.affects_version = ""  # No version
        mock_client.epic_field = "customfield_10000"
        mock_client.jira_url = "https://jira.example.com"

        # Mock API responses
        mock_client.request.side_effect = [
            # GET old issue
            {"fields": {"summary": "Epic Summary", "description": "Epic Description"}},
            # POST create new issue
            {"key": "TEST-789"},
            # POST add comment
            {},
            # GET transitions
            {"transitions": []},  # No transitions available
        ]

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", new_type="epic")

        assert result == {"new_key": "TEST-789"}

        # Verify epic field was set
        create_call = mock_client.request.call_args_list[1]
        payload = create_call[1]["json_data"]["fields"]
        assert payload["customfield_10000"] == "Epic Summary"
        assert "versions" not in payload  # No version should be set

    def test_rest_operation_no_fields(self):
        """Test REST operation when old issue has no fields."""
        plugin = MigratePlugin()
        mock_client = Mock()

        # Set up client attributes
        mock_client.project_key = "TEST"
        mock_client.priority = "Normal"
        mock_client.component_name = "Backend"
        mock_client.affects_version = ""
        mock_client.epic_field = "customfield_10000"
        mock_client.jira_url = "https://jira.example.com"

        # Mock API responses with missing fields
        mock_client.request.side_effect = [
            # GET old issue with empty fields
            {"fields": {}},
            # POST create new issue
            {"key": "TEST-999"},
            # POST add comment
            {},
            # GET transitions with fallback
            {"transitions": [{"id": "3", "name": "In Progress"}]},
            # POST transition
            {},
        ]

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", new_type="task")

        assert result == {"new_key": "TEST-999"}

        # Verify default values were used
        create_call = mock_client.request.call_args_list[1]
        payload = create_call[1]["json_data"]["fields"]
        assert payload["summary"] == "Migrated from TEST-123"
        assert payload["description"] == "Migrated from TEST-123"

    def test_rest_operation_transition_fallback(self):
        """Test REST operation with transition name not found."""
        plugin = MigratePlugin()
        mock_client = Mock()

        # Set up client attributes
        mock_client.project_key = "TEST"
        mock_client.priority = "Normal"
        mock_client.component_name = "Backend"
        mock_client.affects_version = ""
        mock_client.epic_field = "customfield_10000"
        mock_client.jira_url = "https://jira.example.com"

        # Mock API responses
        mock_client.request.side_effect = [
            # GET old issue
            {"fields": {"summary": "Test", "description": "Test"}},
            # POST create new issue
            {"key": "TEST-111"},
            # POST add comment
            {},
            # GET transitions - no done/closed/cancelled
            {
                "transitions": [
                    {"id": "5", "name": "Review"},
                    {"id": "6", "name": "Approved"},
                ]
            },
            # POST transition with first available
            {},
        ]

        plugin.rest_operation(mock_client, issue_key="TEST-123", new_type="story")

        # Verify first transition was used
        transition_call = mock_client.request.call_args_list[4]
        assert transition_call[0][0] == "POST"
        assert transition_call[0][1] == "/rest/api/2/issue/TEST-123/transitions"
        assert transition_call[1]["json_data"]["transition"]["id"] == "5"

    def test_rest_operation_api_error(self):
        """Test REST operation when API call fails."""
        plugin = MigratePlugin()
        mock_client = Mock()
        mock_client.request.side_effect = Exception("API Error")

        with pytest.raises(MigrateError) as exc_info:
            plugin.rest_operation(mock_client, issue_key="TEST-123", new_type="bug")

        assert "Migration failed: API Error" in str(exc_info.value)

    def test_execute_success(self):
        """Test successful execution of migrate command."""
        plugin = MigratePlugin()
        mock_client = Mock()
        mock_client.jira_url = "https://jira.example.com"

        # Mock rest_operation to return new key
        plugin.rest_operation = Mock(return_value={"new_key": "TEST-456"})

        args = Namespace(issue_key="TEST-123", new_type="bug")

        result = plugin.execute(mock_client, args)

        assert result is True
        plugin.rest_operation.assert_called_once_with(mock_client, issue_key="TEST-123", new_type="bug")

    def test_execute_success_same_key(self):
        """Test successful execution when new key is not provided."""
        plugin = MigratePlugin()
        mock_client = Mock()
        mock_client.jira_url = "https://jira.example.com"

        # Mock rest_operation to return empty dict (no new_key)
        plugin.rest_operation = Mock(return_value={})

        args = Namespace(issue_key="TEST-123", new_type="bug")

        result = plugin.execute(mock_client, args)

        assert result is True
        # Should use original key in print message

    def test_execute_failure(self):
        """Test execution when migration fails."""
        plugin = MigratePlugin()
        mock_client = Mock()

        # Mock rest_operation to raise error
        plugin.rest_operation = Mock(side_effect=MigrateError("Failed"))

        args = Namespace(issue_key="TEST-123", new_type="bug")

        with pytest.raises(MigrateError):
            plugin.execute(mock_client, args)

    def test_execute_prints_success(self, capsys):
        """Test that success message is printed correctly."""
        plugin = MigratePlugin()
        mock_client = Mock()
        mock_client.jira_url = "https://jira.example.com"

        plugin.rest_operation = Mock(return_value={"new_key": "TEST-456"})

        args = Namespace(issue_key="TEST-123", new_type="bug")

        plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "✅ Migrated TEST-123 to TEST-456: https://jira.example.com/browse/TEST-456" in captured.out

    def test_execute_prints_error(self, capsys):
        """Test that error message is printed correctly."""
        plugin = MigratePlugin()
        mock_client = Mock()

        plugin.rest_operation = Mock(side_effect=MigrateError("API failed"))

        args = Namespace(issue_key="TEST-123", new_type="bug")

        with pytest.raises(MigrateError):
            plugin.execute(mock_client, args)

        captured = capsys.readouterr()
        assert "❌ Migration failed: API failed" in captured.out
