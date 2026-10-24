#!/usr/bin/env python
"""Tests for the list fields plugin."""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import MissingConfigVariable
from jira_creator.plugins.list_fields_plugin import (
    FIELD_ENV_VARS,
    ListFieldsError,
    ListFieldsPlugin,
)

SAMPLE_FIELDS = [
    {"id": "summary", "name": "Summary", "custom": False},
    {"id": "description", "name": "Description", "custom": False},
    {"id": "customfield_10001", "name": "Epic Link", "custom": True},
    {"id": "customfield_10002", "name": "Story Points", "custom": True},
    {"id": "customfield_10003", "name": "Sprint", "custom": True},
    {"id": "customfield_10004", "name": "Acceptance Criteria", "custom": True},
    {"id": "customfield_10005", "name": "Blocked", "custom": True},
    {"id": "customfield_10006", "name": "Blocked Reason", "custom": True},
    {"id": "customfield_10007", "name": "Workstream", "custom": True},
    {"id": "customfield_10008", "name": "Epic Name", "custom": True},
]


class TestListFieldsPlugin:
    """Test cases for ListFieldsPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = ListFieldsPlugin()
        assert plugin.command_name == "list-fields"
        assert plugin.help_text == "List custom fields from the Jira instance"
        assert plugin.category == "Search & View"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = ListFieldsPlugin()
        mock_parser = Mock(spec=ArgumentParser)

        plugin.register_arguments(mock_parser)

        assert mock_parser.add_argument.call_count == 3

    def test_example_commands(self):
        """Test example commands are provided."""
        plugin = ListFieldsPlugin()
        assert len(plugin.example_commands) > 0
        assert "list-fields" in plugin.example_commands

    def test_get_plugin_exceptions(self):
        """Test plugin exceptions are registered."""
        plugin = ListFieldsPlugin()
        exceptions = plugin.get_plugin_exceptions()
        assert "ListFieldsError" in exceptions
        assert exceptions["ListFieldsError"] is ListFieldsError

    def test_rest_operation(self):
        """Test REST operation fetches fields."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.request.return_value = SAMPLE_FIELDS

        result = plugin.rest_operation(mock_client)

        mock_client.request.assert_called_once_with("GET", "/rest/api/2/field")
        assert result == SAMPLE_FIELDS

    def test_execute_all_fields(self, capsys):
        """Test execute displays all fields."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.request.return_value = SAMPLE_FIELDS

        args = Namespace(filter="", custom_only=False, check_config=False)
        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "Summary" in captured.out
        assert "Epic Link" in captured.out
        assert f"Total: {len(SAMPLE_FIELDS)} fields" in captured.out

    def test_execute_custom_only(self, capsys):
        """Test execute with --custom-only filter."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.request.return_value = SAMPLE_FIELDS

        args = Namespace(filter="", custom_only=True, check_config=False)
        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        # Should not contain non-custom fields
        assert "Summary" not in captured.out
        assert "Description" not in captured.out
        # Should contain custom fields
        assert "Epic Link" in captured.out
        custom_count = len([f for f in SAMPLE_FIELDS if f.get("custom")])
        assert f"Total: {custom_count} fields" in captured.out

    def test_execute_filter_by_name(self, capsys):
        """Test execute with --filter."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.request.return_value = SAMPLE_FIELDS

        args = Namespace(filter="sprint", custom_only=False, check_config=False)
        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "Sprint" in captured.out
        assert "Total: 1 fields" in captured.out

    def test_execute_filter_by_id(self, capsys):
        """Test execute with --filter matching field ID."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.request.return_value = SAMPLE_FIELDS

        args = Namespace(filter="customfield_10001", custom_only=False, check_config=False)
        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "Epic Link" in captured.out
        assert "Total: 1 fields" in captured.out

    def test_execute_filter_case_insensitive(self, capsys):
        """Test filter is case-insensitive."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.request.return_value = SAMPLE_FIELDS

        args = Namespace(filter="EPIC", custom_only=False, check_config=False)
        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "Epic Link" in captured.out
        assert "Epic Name" in captured.out

    def test_execute_no_results(self, capsys):
        """Test execute when no fields match filter."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.request.return_value = SAMPLE_FIELDS

        args = Namespace(filter="nonexistent", custom_only=False, check_config=False)
        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "No fields found matching your criteria." in captured.out

    def test_execute_empty_fields(self, capsys):
        """Test execute when instance returns no fields."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.request.return_value = []

        args = Namespace(filter="", custom_only=False, check_config=False)
        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "No fields found matching your criteria." in captured.out

    @patch("jira_creator.plugins.list_fields_plugin.EnvFetcher")
    def test_execute_check_config_all_ok(self, mock_env_fetcher, capsys):
        """Test --check-config when all fields are correctly configured."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.is_cloud = True
        mock_client.request.return_value = SAMPLE_FIELDS

        # Map env vars to the sample field IDs
        env_map = {
            "JIRA_EPIC_FIELD": "customfield_10001",
            "JIRA_EPIC_NAME_FIELD": "customfield_10008",
            "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_10004",
            "JIRA_BLOCKED_FIELD": "customfield_10005",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10006",
            "JIRA_STORY_POINTS_FIELD": "customfield_10002",
            "JIRA_SPRINT_FIELD": "customfield_10003",
            "JIRA_WORKSTREAM_FIELD": "customfield_10007",
        }
        mock_env_fetcher.get.side_effect = lambda key, default="": env_map.get(key, default)

        args = Namespace(filter="", custom_only=False, check_config=True)
        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "Cloud" in captured.out
        assert captured.out.count("OK") == len(FIELD_ENV_VARS)

    @patch("jira_creator.plugins.list_fields_plugin.EnvFetcher")
    def test_execute_check_config_missing_field(self, mock_env_fetcher, capsys):
        """Test --check-config when a configured field doesn't exist on instance."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.is_cloud = True
        mock_client.request.return_value = SAMPLE_FIELDS

        # One field points to a non-existent ID
        env_map = {
            "JIRA_EPIC_FIELD": "customfield_99999",
            "JIRA_EPIC_NAME_FIELD": "customfield_10008",
            "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_10004",
            "JIRA_BLOCKED_FIELD": "customfield_10005",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10006",
            "JIRA_STORY_POINTS_FIELD": "customfield_10002",
            "JIRA_SPRINT_FIELD": "customfield_10003",
            "JIRA_WORKSTREAM_FIELD": "customfield_10007",
        }
        mock_env_fetcher.get.side_effect = lambda key, default="": env_map.get(key, default)

        args = Namespace(filter="", custom_only=False, check_config=True)
        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "FIELD NOT FOUND" in captured.out
        assert "customfield_99999" in captured.out
        # Should suggest the correct field
        assert "Suggestion" in captured.out
        assert "customfield_10001" in captured.out

    @patch("jira_creator.plugins.list_fields_plugin.EnvFetcher")
    def test_execute_check_config_not_configured(self, mock_env_fetcher, capsys):
        """Test --check-config when env var is not set."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.is_cloud = False
        mock_client.request.return_value = SAMPLE_FIELDS

        # Return empty for all env vars
        mock_env_fetcher.get.return_value = ""

        args = Namespace(filter="", custom_only=False, check_config=True)
        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "Data Center/Server" in captured.out
        assert "NOT CONFIGURED" in captured.out

    @patch("jira_creator.plugins.list_fields_plugin.EnvFetcher")
    def test_execute_check_config_env_fetcher_exception(self, mock_env_fetcher, capsys):
        """Test --check-config when EnvFetcher raises an exception."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.is_cloud = True
        mock_client.request.return_value = SAMPLE_FIELDS

        mock_env_fetcher.get.side_effect = MissingConfigVariable("Missing env var")

        args = Namespace(filter="", custom_only=False, check_config=True)
        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "NOT CONFIGURED" in captured.out

    def test_execute_api_error(self):
        """Test execute when API call fails."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = ListFieldsError("Connection failed")

        args = Namespace(filter="", custom_only=False, check_config=False)

        with pytest.raises(ListFieldsError):
            plugin.execute(mock_client, args)


class TestListFieldsPluginHelpers:
    """Tests for ListFieldsPlugin helper methods and constants."""

    def test_display_fields_sorted(self, capsys):
        """Test fields are displayed sorted by ID."""
        plugin = ListFieldsPlugin()
        unsorted_fields = [
            {"id": "customfield_10003", "name": "Sprint", "custom": True},
            {"id": "customfield_10001", "name": "Epic Link", "custom": True},
        ]

        plugin.display_fields(unsorted_fields)

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        # Find the data lines (after header and separator)
        data_lines = [line for line in lines if line.startswith("customfield_")]
        assert "customfield_10001" in data_lines[0]
        assert "customfield_10003" in data_lines[1]

    def test_display_fields_missing_keys(self, capsys):
        """Test display handles fields with missing keys."""
        plugin = ListFieldsPlugin()
        fields = [{"id": "test_field"}, {"name": "No ID Field"}]

        plugin.display_fields(fields)

        captured = capsys.readouterr()
        assert "Total: 2 fields" in captured.out

    def test_execute_custom_only_with_filter(self, capsys):
        """Test combining --custom-only and --filter."""
        plugin = ListFieldsPlugin()
        mock_client = Mock()
        mock_client.request.return_value = SAMPLE_FIELDS

        args = Namespace(filter="epic", custom_only=True, check_config=False)
        result = plugin.execute(mock_client, args)

        assert result is True
        captured = capsys.readouterr()
        assert "Epic Link" in captured.out
        assert "Epic Name" in captured.out
        assert "Summary" not in captured.out

    def test_field_env_vars_constant(self):
        """Test FIELD_ENV_VARS contains expected entries."""
        assert "JIRA_EPIC_FIELD" in FIELD_ENV_VARS
        assert "JIRA_STORY_POINTS_FIELD" in FIELD_ENV_VARS
        assert "JIRA_SPRINT_FIELD" in FIELD_ENV_VARS
        assert "JIRA_WORKSTREAM_FIELD" in FIELD_ENV_VARS
        assert "JIRA_BLOCKED_FIELD" in FIELD_ENV_VARS
        assert "JIRA_BLOCKED_REASON_FIELD" in FIELD_ENV_VARS
        assert "JIRA_ACCEPTANCE_CRITERIA_FIELD" in FIELD_ENV_VARS
        assert "JIRA_EPIC_NAME_FIELD" in FIELD_ENV_VARS
        assert len(FIELD_ENV_VARS) == 8

    def test_check_single_field_ok(self, capsys):
        """Test check_single_field with a valid field."""
        ListFieldsPlugin.check_single_field(
            "JIRA_EPIC_FIELD",
            "Epic Link",
            "customfield_10001",
            {"customfield_10001": "Epic Link"},
            {"epic link": ["customfield_10001"]},
        )

        captured = capsys.readouterr()
        assert "OK" in captured.out
        assert "customfield_10001" in captured.out

    def test_check_single_field_not_found_with_suggestion(self, capsys):
        """Test check_single_field with a missing field that has suggestions."""
        ListFieldsPlugin.check_single_field(
            "JIRA_EPIC_FIELD",
            "Epic Link",
            "customfield_99999",
            {"customfield_10001": "Epic Link"},
            {"epic link": ["customfield_10001"]},
        )

        captured = capsys.readouterr()
        assert "FIELD NOT FOUND" in captured.out
        assert "Suggestion" in captured.out
        assert "customfield_10001" in captured.out

    def test_check_single_field_not_configured_with_suggestion(self, capsys):
        """Test check_single_field when not configured but suggestions exist."""
        ListFieldsPlugin.check_single_field(
            "JIRA_SPRINT_FIELD",
            "Sprint",
            None,
            {"customfield_10003": "Sprint"},
            {"sprint": ["customfield_10003"]},
        )

        captured = capsys.readouterr()
        assert "NOT CONFIGURED" in captured.out
        assert "Suggestion" in captured.out
        assert "customfield_10003" in captured.out

    def test_check_single_field_not_configured_no_suggestion(self, capsys):
        """Test check_single_field when not configured and no suggestions."""
        ListFieldsPlugin.check_single_field(
            "JIRA_WORKSTREAM_FIELD",
            "Workstream",
            None,
            {},
            {},
        )

        captured = capsys.readouterr()
        assert "NOT CONFIGURED" in captured.out
        assert "Suggestion" not in captured.out
