#!/usr/bin/env python
"""Tests for the set acceptance criteria plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import SetAcceptanceCriteriaError
from jira_creator.plugins.set_acceptance_criteria_plugin import (
    SetAcceptanceCriteriaPlugin,
)


class TestSetAcceptanceCriteriaPlugin:
    """Test cases for SetAcceptanceCriteriaPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = SetAcceptanceCriteriaPlugin()
        assert plugin.command_name == "set-acceptance-criteria"
        assert plugin.help_text == "Set the acceptance criteria for a Jira issue"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        # Verify add_argument was called with correct parameters
        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list

        # First argument: issue_key
        assert calls[0][0] == ("issue_key",)
        assert calls[0][1]["help"] == "The Jira issue key (e.g., PROJ-123)"

        # Second argument: acceptance_criteria (with nargs="*")
        assert calls[1][0] == ("acceptance_criteria",)
        assert calls[1][1]["nargs"] == "*"
        assert calls[1][1]["help"] == "The acceptance criteria (can be multiple words)"

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_rest_operation(self, mock_env_fetcher):
        """Test the REST operation directly."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        # Mock EnvFetcher.get to return acceptance criteria field
        mock_env_fetcher.get.return_value = "customfield_10050"

        result = plugin.rest_operation(
            mock_client,
            issue_key="TEST-123",
            acceptance_criteria="User can login successfully",
        )

        # Verify EnvFetcher was called
        mock_env_fetcher.get.assert_called_once_with("JIRA_ACCEPTANCE_CRITERIA_FIELD")

        # Verify the request
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10050": "User can login successfully"}},
        )
        assert result == {"key": "TEST-123"}

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_execute_success(self, mock_env_fetcher, capsys):
        """Test successful execution with acceptance criteria."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        mock_env_fetcher.get.return_value = "customfield_10050"

        args = Namespace(
            issue_key="TEST-123",
            acceptance_criteria=["User", "can", "login", "successfully"],
        )

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10050": "User can login successfully"}},
        )

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Acceptance criteria set for TEST-123" in captured.out

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_execute_with_empty_criteria(self, mock_env_fetcher, capsys):
        """Test execution with empty acceptance criteria."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        mock_env_fetcher.get.return_value = "customfield_10050"

        args = Namespace(issue_key="TEST-123", acceptance_criteria=[])

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10050": ""}},
        )

        # Verify print output
        captured = capsys.readouterr()
        assert "⚠️  No acceptance criteria provided. Setting to empty." in captured.out
        assert "✅ Acceptance criteria cleared for TEST-123" in captured.out

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_execute_with_whitespace_only(self, mock_env_fetcher, capsys):
        """Test execution with whitespace-only acceptance criteria."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        mock_env_fetcher.get.return_value = "customfield_10050"

        args = Namespace(issue_key="TEST-123", acceptance_criteria=["   ", "\t", "\n"])

        result = plugin.execute(mock_client, args)

        # Verify success - whitespace should be treated as empty
        assert result is True
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123",
            json_data={"fields": {"customfield_10050": ""}},
        )

        # Verify print output
        captured = capsys.readouterr()
        assert "⚠️  No acceptance criteria provided. Setting to empty." in captured.out
        assert "✅ Acceptance criteria cleared for TEST-123" in captured.out

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_execute_failure(self, mock_env_fetcher, capsys):
        """Test execution with API failure."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = SetAcceptanceCriteriaError("Field not found")

        mock_env_fetcher.get.return_value = "customfield_10050"

        args = Namespace(
            issue_key="TEST-123",
            acceptance_criteria=["Must", "handle", "errors"],
        )

        # Verify exception is raised
        with pytest.raises(SetAcceptanceCriteriaError) as exc_info:
            plugin.execute(mock_client, args)

        # Verify the exception message
        assert str(exc_info.value) == "Field not found"

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to set acceptance criteria: Field not found" in captured.out

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_execute_with_multiline_criteria(self, mock_env_fetcher):
        """Test execute with multiline acceptance criteria."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}
        mock_env_fetcher.get.return_value = "customfield_10050"

        # Test with words that will form multiline criteria
        args = Namespace(
            issue_key="TEST-123",
            acceptance_criteria=[
                "Given",
                "user",
                "is",
                "logged",
                "in\\nWhen",
                "they",
                "click",
                "submit\\nThen",
                "form",
                "is",
                "saved",
            ],
        )

        result = plugin.execute(mock_client, args)

        assert result is True
        # Verify the criteria was joined properly
        call_args = mock_client.request.call_args[1]["json_data"]
        expected = "Given user is logged in\\nWhen they click submit\\nThen form is saved"
        assert call_args["fields"]["customfield_10050"] == expected

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_execute_with_special_characters(self, mock_env_fetcher):
        """Test execute with acceptance criteria containing special characters."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}
        mock_env_fetcher.get.return_value = "customfield_10050"

        # Test different special character scenarios
        test_cases = [
            (
                ["User", "enters", '"quoted"', "text"],
                'User enters "quoted" text',
            ),
            (
                ["Handle", "&", "ampersand", "character"],
                "Handle & ampersand character",
            ),
            (
                ["Support", "<tags>", "in", "criteria"],
                "Support <tags> in criteria",
            ),
            (
                ["Path:", "/usr/local/bin"],
                "Path: /usr/local/bin",
            ),
            (
                ["Email:", "user@example.com"],
                "Email: user@example.com",
            ),
        ]

        for criteria_list, expected in test_cases:
            mock_client.reset_mock()
            args = Namespace(issue_key="TEST-123", acceptance_criteria=criteria_list)

            result = plugin.execute(mock_client, args)

            assert result is True
            # Verify the criteria was joined correctly
            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["fields"]["customfield_10050"] == expected

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_rest_operation_with_empty_string(self, mock_env_fetcher):
        """Test REST operation with empty string criteria."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()
        mock_env_fetcher.get.return_value = "customfield_10050"

        plugin.rest_operation(mock_client, issue_key="TEST-456", acceptance_criteria="")

        # Verify empty string is passed through
        call_args = mock_client.request.call_args[1]["json_data"]
        assert call_args["fields"]["customfield_10050"] == ""

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_execute_with_very_long_criteria(self, mock_env_fetcher):
        """Test execute with very long acceptance criteria."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}
        mock_env_fetcher.get.return_value = "customfield_10050"

        # Create a very long criteria
        long_words = ["word"] * 100  # 100 words
        args = Namespace(issue_key="TEST-123", acceptance_criteria=long_words)

        result = plugin.execute(mock_client, args)

        assert result is True
        # Verify the criteria was joined correctly
        call_args = mock_client.request.call_args[1]["json_data"]
        expected = " ".join(long_words)
        assert call_args["fields"]["customfield_10050"] == expected
        assert len(call_args["fields"]["customfield_10050"]) > 400  # Verify it's long

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_env_fetcher_returns_different_field(self, mock_env_fetcher):
        """Test that the plugin uses the field returned by EnvFetcher."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()

        # Test with different custom field IDs
        custom_fields = [
            "customfield_10050",
            "customfield_20060",
            "acceptance_criteria_field",
        ]

        for field_id in custom_fields:
            mock_client.reset_mock()
            mock_env_fetcher.get.return_value = field_id

            plugin.rest_operation(
                mock_client,
                issue_key="TEST-123",
                acceptance_criteria="Test criteria",
            )

            # Verify the correct field ID was used
            call_args = mock_client.request.call_args[1]["json_data"]
            assert field_id in call_args["fields"]
            assert call_args["fields"][field_id] == "Test criteria"

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_execute_with_unicode_characters(self, mock_env_fetcher, capsys):
        """Test execute with Unicode characters in acceptance criteria."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}
        mock_env_fetcher.get.return_value = "customfield_10050"

        args = Namespace(
            issue_key="TEST-123",
            acceptance_criteria=["User", "sees", "émojis", "🚀", "correctly"],
        )

        result = plugin.execute(mock_client, args)

        assert result is True
        # Verify Unicode is preserved
        call_args = mock_client.request.call_args[1]["json_data"]
        assert call_args["fields"]["customfield_10050"] == "User sees émojis 🚀 correctly"

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Acceptance criteria set for TEST-123" in captured.out
