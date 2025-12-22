#!/usr/bin/env python
"""Tests for the set acceptance criteria plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import AiError
from jira_creator.plugins.set_acceptance_criteria_plugin import SetAcceptanceCriteriaError, SetAcceptanceCriteriaPlugin


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
        assert mock_parser.add_argument.call_count == 3
        calls = mock_parser.add_argument.call_args_list

        # First argument: issue_key
        assert calls[0][0] == ("issue_key",)
        assert calls[0][1]["help"] == "The Jira issue key (e.g., PROJ-123)"

        # Second argument: acceptance_criteria (with nargs="*")
        assert calls[1][0] == ("acceptance_criteria",)
        assert calls[1][1]["nargs"] == "*"
        assert calls[1][1]["help"] == "The acceptance criteria (can be multiple words)"

        # Third argument: --ai-from-description
        assert calls[2][0] == ("--ai-from-description",)
        assert calls[2][1]["action"] == "store_true"

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
            ai_from_description=False,
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

        args = Namespace(ai_from_description=False, issue_key="TEST-123", acceptance_criteria=[])

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

        args = Namespace(ai_from_description=False, issue_key="TEST-123", acceptance_criteria=["   ", "\t", "\n"])

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
            ai_from_description=False,
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
            ai_from_description=False,
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
            args = Namespace(ai_from_description=False, issue_key="TEST-123", acceptance_criteria=criteria_list)

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
        args = Namespace(ai_from_description=False, issue_key="TEST-123", acceptance_criteria=long_words)

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
            ai_from_description=False,
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

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.get_ai_provider")
    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_execute_with_ai_from_description_success(self, mock_env, mock_get_ai, capsys):
        """Test execute with AI generation from description."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()

        mock_env.get.side_effect = lambda key, default="": {
            "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_10050",
            "JIRA_AI_PROVIDER": "openai",
        }.get(key, default)

        mock_ai = Mock()
        mock_ai.complete.return_value = "* [ ] User can login\n* [ ] Password is validated"
        mock_get_ai.return_value = mock_ai

        # Mock API responses
        mock_client.request.side_effect = [
            # Fetch issue
            {"fields": {"description": "User login feature", "summary": "Login"}},
            # Update AC
            {"key": "TEST-123"},
        ]

        args = Namespace(ai_from_description=True, issue_key="TEST-123", acceptance_criteria=[])

        result = plugin.execute(mock_client, args)

        assert result is True
        mock_ai.complete.assert_called_once()

        captured = capsys.readouterr()
        assert "Generating acceptance criteria from description" in captured.out
        assert "Acceptance criteria set for TEST-123" in captured.out
        assert "Generated Acceptance Criteria" in captured.out

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.get_ai_provider")
    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_generate_from_description_no_description(self, mock_env, mock_get_ai):
        """Test AI generation when issue has no description."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()

        mock_env.get.return_value = "openai"

        mock_client.request.return_value = {"fields": {"description": "", "summary": "Test"}}

        with pytest.raises(SetAcceptanceCriteriaError, match="has no description to generate from"):
            plugin._generate_from_description(mock_client, "TEST-123")

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.get_ai_provider")
    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_generate_from_description_ai_empty(self, mock_env, mock_get_ai):
        """Test AI generation when AI returns empty criteria."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()

        mock_env.get.return_value = "openai"

        mock_ai = Mock()
        mock_ai.complete.return_value = "   "
        mock_get_ai.return_value = mock_ai

        mock_client.request.return_value = {"fields": {"description": "Test desc", "summary": "Test"}}

        with pytest.raises(SetAcceptanceCriteriaError, match="AI generated empty acceptance criteria"):
            plugin._generate_from_description(mock_client, "TEST-123")

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.get_ai_provider")
    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_generate_from_description_ai_error(self, mock_env, mock_get_ai):
        """Test AI generation when AI provider fails."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()

        mock_env.get.return_value = "openai"

        mock_get_ai.side_effect = AiError("AI service unavailable")

        mock_client.request.return_value = {"fields": {"description": "Test", "summary": "Test"}}

        with pytest.raises(SetAcceptanceCriteriaError, match="AI generation failed"):
            plugin._generate_from_description(mock_client, "TEST-123")

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.get_ai_provider")
    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_generate_from_description_fetch_error(self, mock_env, mock_get_ai):
        """Test AI generation when fetching issue fails."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()

        mock_env.get.return_value = "openai"

        mock_client.request.side_effect = Exception("Network error")

        with pytest.raises(SetAcceptanceCriteriaError, match="Failed to generate acceptance criteria"):
            plugin._generate_from_description(mock_client, "TEST-123")

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.get_ai_provider")
    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher")
    def test_execute_with_ai_from_description_error(self, mock_env, mock_get_ai):
        """Test execute with AI generation error."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()

        mock_env.get.side_effect = lambda key, default="": {
            "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_10050",
            "JIRA_AI_PROVIDER": "openai",
        }.get(key, default)

        mock_client.request.side_effect = Exception("API Error")

        args = Namespace(ai_from_description=True, issue_key="TEST-123", acceptance_criteria=[])

        # Exception is raised from _generate_from_description before try block
        with pytest.raises(SetAcceptanceCriteriaError):
            plugin.execute(mock_client, args)

    def test_get_fix_capabilities(self):
        """Test get_fix_capabilities returns expected capabilities - covers line 169."""
        plugin = SetAcceptanceCriteriaPlugin()

        capabilities = plugin.get_fix_capabilities()

        assert isinstance(capabilities, list)
        assert len(capabilities) == 1
        assert capabilities[0]["method_name"] == "set_acceptance_criteria_from_description"
        assert "description" in capabilities[0]
        assert "params" in capabilities[0]
        assert "conditions" in capabilities[0]

    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.EnvFetcher.get")
    @patch("jira_creator.plugins.set_acceptance_criteria_plugin.get_ai_provider")
    def test_execute_fix_success(self, mock_get_ai_provider, mock_env):
        """Test execute_fix with successful execution - covers lines 194-200."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()

        # Mock AI provider
        mock_ai = Mock()
        mock_ai.improve_text.return_value = "Generated criteria"
        mock_get_ai_provider.return_value = mock_ai

        # Mock environment
        mock_env.side_effect = lambda key, default="": {
            "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_10050",
            "JIRA_AI_PROVIDER": "openai",
        }.get(key, default)

        # Mock client responses
        mock_client.request.side_effect = [
            {
                "key": "TEST-123",
                "fields": {"description": "Test description", "customfield_10050": ""},
            },
            {"key": "TEST-123"},
        ]

        args = {"issue_key": "TEST-123"}
        result = plugin.execute_fix(mock_client, "set_acceptance_criteria_from_description", args)

        assert result is True

    def test_execute_fix_with_exception(self):
        """Test execute_fix with exception - covers lines 199-200."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()

        # Patch execute method to raise an exception
        with patch.object(plugin, "execute", side_effect=Exception("Test error")):
            args = {"issue_key": "TEST-123"}
            result = plugin.execute_fix(mock_client, "set_acceptance_criteria_from_description", args)

            assert result is False

    def test_execute_fix_unknown_method(self):
        """Test execute_fix with unknown method - covers line 202."""
        plugin = SetAcceptanceCriteriaPlugin()
        mock_client = Mock()

        args = {"issue_key": "TEST-123"}
        result = plugin.execute_fix(mock_client, "unknown_method", args)

        assert result is False
