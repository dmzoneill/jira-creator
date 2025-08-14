#!/usr/bin/env python
"""Tests for the validate issue plugin."""

from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.plugins.validate_issue_plugin import ValidateIssuePlugin


class TestValidateIssuePlugin:
    """Test cases for ValidateIssuePlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = ValidateIssuePlugin()
        assert plugin.command_name == "validate-issue"
        assert plugin.help_text == "Validate a Jira issue against quality standards"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = ValidateIssuePlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        # Verify all arguments are registered
        assert mock_parser.add_argument.call_count == 3

        # Check specific argument calls
        calls = mock_parser.add_argument.call_args_list
        assert calls[0][0] == ("issue_key",)
        assert calls[0][1]["help"] == "The Jira issue key (e.g., PROJ-123)"

        assert calls[1][0] == ("--no-ai",)
        assert calls[1][1]["action"] == "store_true"
        assert calls[1][1]["help"] == "Skip AI-powered quality checks"

        assert calls[2][0] == ("--no-cache",)
        assert calls[2][1]["action"] == "store_true"
        assert calls[2][1]["help"] == "Skip cache and force fresh validation"

    def test_rest_operation(self):
        """Test the REST operation."""
        plugin = ValidateIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"fields": {"summary": "Test Issue"}}

        result = plugin.rest_operation(mock_client, issue_key="TEST-123")

        mock_client.request.assert_called_once_with("GET", "/rest/api/2/issue/TEST-123")
        assert result == {"fields": {"summary": "Test Issue"}}

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_execute_successful_no_issues(self, mock_env_fetcher):
        """Test successful execution with no validation issues."""
        # Setup environment variable mocks
        mock_env_fetcher.get.return_value = ""

        plugin = ValidateIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {
            "fields": {
                "summary": "Test Issue Summary",
                "description": "This is a detailed description with more than 50 characters",
                "status": {"name": "To Do"},
                "assignee": {"displayName": "John Doe"},
                "priority": {"name": "High"},
                "issuetype": {"name": "task"},
            }
        }

        args = Namespace(issue_key="TEST-123", no_ai=True, no_cache=False)

        # Capture print output
        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is True
        mock_client.request.assert_called_once()
        mock_print.assert_called_with("✅ TEST-123 passed all validations")

    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_execute_with_validation_issues(self, mock_env_fetcher, mock_get_ai_provider):
        """Test execution with validation issues."""
        # Setup environment variable mocks
        mock_env_fetcher.get.side_effect = lambda key, default="": {
            "JIRA_EPIC_FIELD": "customfield_10001",
            "JIRA_SPRINT_FIELD": "customfield_10002",
            "JIRA_STORY_POINTS_FIELD": "customfield_10003",
            "JIRA_BLOCKED_FIELD": "customfield_10004",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10005",
            "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_10006",
            "JIRA_AI_PROVIDER": "openai",
        }.get(key, default)

        # Mock AI provider
        mock_ai_provider = Mock()
        mock_get_ai_provider.return_value = mock_ai_provider

        plugin = ValidateIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {
            "fields": {
                "summary": "Test Issue Summary",
                "description": "Short desc",  # Too short
                "status": {"name": "In Progress"},
                "assignee": None,  # Missing assignee for In Progress
                "priority": {},  # Empty dict instead of None to avoid AttributeError
                "issuetype": {"name": "story"},
                "customfield_10001": None,  # Missing epic
                "customfield_10002": None,  # Missing sprint
                "customfield_10003": None,  # Missing story points
                "customfield_10004": {"value": "True"},  # Blocked
                "customfield_10005": "",  # No blocked reason
                "customfield_10006": "AC",  # Too short AC
            }
        }

        args = Namespace(issue_key="TEST-123", no_ai=False, no_cache=False)

        # Capture print output
        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        assert result is False

        # Verify error output
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("❌ Validation failed for TEST-123" in str(call) for call in print_calls)
        assert any("📊 Total issues:" in str(call) for call in print_calls)

    def test_execute_with_exception(self):
        """Test execution with API error."""
        plugin = ValidateIssuePlugin()
        mock_client = Mock()
        mock_client.request.side_effect = Exception("API failed")

        args = Namespace(issue_key="TEST-123", no_ai=True, no_cache=False)

        with patch("builtins.print") as mock_print:
            with pytest.raises(Exception) as exc_info:
                plugin.execute(mock_client, args)

        assert "Failed to validate issue: API failed" in str(exc_info.value)
        mock_print.assert_called_with("❌ Failed to validate issue: API failed")

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_run_validations_in_progress_no_assignee(self, mock_env_fetcher):
        """Test validation for In Progress issue without assignee."""
        mock_env_fetcher.get.return_value = ""

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "In Progress"},
            "assignee": None,
            "priority": {"name": "High"},
            "issuetype": {"name": "task"},
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Issue is 'In Progress' but not assigned to anyone" in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_run_validations_story_no_epic(self, mock_env_fetcher):
        """Test validation for story without epic."""
        mock_env_fetcher.get.side_effect = lambda key, default="": {"JIRA_EPIC_FIELD": "customfield_10001"}.get(
            key, default
        )

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "To Do"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "story"},
            "customfield_10001": None,
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Story is not linked to an epic" in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_run_validations_in_progress_no_sprint(self, mock_env_fetcher):
        """Test validation for In Progress issue without sprint."""
        mock_env_fetcher.get.side_effect = lambda key, default="": {"JIRA_SPRINT_FIELD": "customfield_10002"}.get(
            key, default
        )

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "task"},
            "customfield_10002": None,
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Issue is 'In Progress' but not in a sprint" in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_run_validations_no_priority(self, mock_env_fetcher):
        """Test validation for issue without priority."""
        mock_env_fetcher.get.return_value = ""

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "To Do"},
            "assignee": {"displayName": "User"},
            "priority": {},  # Empty dict instead of None
            "issuetype": {"name": "task"},
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Issue has no priority set" in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_run_validations_priority_with_none_name(self, mock_env_fetcher):
        """Test validation for issue with priority but None name."""
        mock_env_fetcher.get.return_value = ""

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "To Do"},
            "assignee": {"displayName": "User"},
            "priority": {"name": None},  # Priority exists but name is None
            "issuetype": {"name": "task"},
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Issue has no priority set" in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_run_validations_story_no_points(self, mock_env_fetcher):
        """Test validation for story without story points."""
        mock_env_fetcher.get.side_effect = lambda key, default="": {"JIRA_STORY_POINTS_FIELD": "customfield_10003"}.get(
            key, default
        )

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "To Do"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "story"},
            "customfield_10003": None,
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Story has no story points" in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_run_validations_bug_no_points(self, mock_env_fetcher):
        """Test validation for bug without story points."""
        mock_env_fetcher.get.side_effect = lambda key, default="": {"JIRA_STORY_POINTS_FIELD": "customfield_10003"}.get(
            key, default
        )

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "To Do"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "bug"},
            "customfield_10003": None,
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Bug has no story points" in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_run_validations_closed_story_no_points_ok(self, mock_env_fetcher):
        """Test that closed stories don't need story points."""
        mock_env_fetcher.get.side_effect = lambda key, default="": {"JIRA_STORY_POINTS_FIELD": "customfield_10003"}.get(
            key, default
        )

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "Closed"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "story"},
            "customfield_10003": None,
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Story has no story points" not in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_run_validations_blocked_no_reason(self, mock_env_fetcher):
        """Test validation for blocked issue without reason."""
        mock_env_fetcher.get.side_effect = lambda key, default="": {
            "JIRA_BLOCKED_FIELD": "customfield_10004",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10005",
        }.get(key, default)

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "To Do"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "task"},
            "customfield_10004": {"value": "True"},
            "customfield_10005": "   ",  # Whitespace only
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Issue is blocked but has no reason" in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_run_validations_blocked_with_id(self, mock_env_fetcher):
        """Test validation for blocked issue using ID format."""
        mock_env_fetcher.get.side_effect = lambda key, default="": {
            "JIRA_BLOCKED_FIELD": "customfield_10004",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10005",
        }.get(key, default)

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "To Do"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "task"},
            "customfield_10004": {"id": "14656"},  # Blocked ID
            "customfield_10005": None,
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Issue is blocked but has no reason" in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_run_validations_with_ai(self, mock_env_fetcher):
        """Test validation with AI checks enabled."""
        mock_env_fetcher.get.side_effect = lambda key, default="": {
            "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_10006",
            "JIRA_AI_PROVIDER": "openai",
        }.get(key, default)

        plugin = ValidateIssuePlugin()

        # Mock AI provider
        mock_ai_provider = Mock()
        plugin._injected_deps = {"ai_provider": mock_ai_provider}

        fields = {
            "status": {"name": "To Do"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "story"},
            "description": "Short",  # Too short
            "customfield_10006": "AC",  # Too short
        }

        issues = plugin._run_validations(fields, "TEST-1", False, False)

        # Should include AI validation issues
        assert "Description is too short (less than 50 characters)" in issues
        assert "Story has missing or insufficient acceptance criteria" in issues

    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_validate_with_ai_description_check(self, mock_env_fetcher, mock_get_ai_provider):
        """Test AI validation for description quality."""
        mock_env_fetcher.get.return_value = ""
        mock_ai_provider = Mock()
        mock_get_ai_provider.return_value = mock_ai_provider

        plugin = ValidateIssuePlugin()

        fields = {
            "description": "Too short description",
            "issuetype": {"name": "story"},
        }

        issues = plugin._validate_with_ai(fields, "TEST-1", "", False)
        assert "Description is too short (less than 50 characters)" in issues

    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_validate_with_ai_acceptance_criteria(self, mock_env_fetcher, mock_get_ai_provider):
        """Test AI validation for acceptance criteria."""
        mock_env_fetcher.get.return_value = ""
        mock_ai_provider = Mock()
        mock_get_ai_provider.return_value = mock_ai_provider

        plugin = ValidateIssuePlugin()

        fields = {
            "description": "This is a very detailed description with more than 50 characters",
            "issuetype": {"name": "story"},
            "customfield_10006": "AC",  # Too short
        }

        issues = plugin._validate_with_ai(fields, "TEST-1", "customfield_10006", False)
        assert "Story has missing or insufficient acceptance criteria" in issues

    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_validate_with_ai_no_description(self, mock_env_fetcher, mock_get_ai_provider):
        """Test AI validation with missing description."""
        mock_env_fetcher.get.return_value = ""
        mock_ai_provider = Mock()
        mock_get_ai_provider.return_value = mock_ai_provider

        plugin = ValidateIssuePlugin()

        fields = {"description": "", "issuetype": {"name": "story"}}

        issues = plugin._validate_with_ai(fields, "TEST-1", "", False)
        # Should not add issue for empty description (handled elsewhere)
        assert "Description is too short" not in issues

    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_validate_with_ai_valid_content(self, mock_env_fetcher, mock_get_ai_provider):
        """Test AI validation with valid content."""
        mock_env_fetcher.get.return_value = ""
        mock_ai_provider = Mock()
        mock_get_ai_provider.return_value = mock_ai_provider

        plugin = ValidateIssuePlugin()

        fields = {
            "description": "This is a very detailed description with more than 50 characters explaining the feature",
            "issuetype": {"name": "story"},
            "customfield_10006": "Given: User is logged in\nWhen: User clicks button\nThen: Action happens",
        }

        issues = plugin._validate_with_ai(fields, "TEST-1", "customfield_10006", False)
        assert len(issues) == 0

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_edge_case_none_values(self, mock_env_fetcher):
        """Test handling of None values in fields - demonstrates current implementation limitation."""
        mock_env_fetcher.get.return_value = ""

        plugin = ValidateIssuePlugin()
        fields = {"status": None, "assignee": None, "priority": None, "issuetype": None}

        # Current implementation doesn't handle None values gracefully
        # This would raise AttributeError: 'NoneType' object has no attribute 'get'
        with pytest.raises(AttributeError):
            plugin._run_validations(fields, "TEST-1", True, False)

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_edge_case_missing_nested_fields(self, mock_env_fetcher):
        """Test handling of missing nested fields."""
        mock_env_fetcher.get.return_value = ""

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {},  # Missing 'name'
            "assignee": {"displayName": "User"},
            "priority": {},  # Missing 'name'
            "issuetype": {},  # Missing 'name'
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Issue has no priority set" in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_all_validations_pass(self, mock_env_fetcher):
        """Test when all validations pass."""
        mock_env_fetcher.get.side_effect = lambda key, default="": {
            "JIRA_EPIC_FIELD": "customfield_10001",
            "JIRA_SPRINT_FIELD": "customfield_10002",
            "JIRA_STORY_POINTS_FIELD": "customfield_10003",
            "JIRA_BLOCKED_FIELD": "customfield_10004",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10005",
            "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_10006",
        }.get(key, default)

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "story"},
            "customfield_10001": "EPIC-123",  # Has epic
            "customfield_10002": ["Sprint 1"],  # Has sprint
            "customfield_10003": "5",  # Has story points
            "customfield_10004": {"value": "False"},  # Not blocked
            "customfield_10006": "Given/When/Then acceptance criteria with sufficient detail",
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert len(issues) == 0

    def test_get_dependency_injected(self):
        """Test getting an injected dependency."""
        mock_ai_provider = Mock()
        plugin = ValidateIssuePlugin(ai_provider=mock_ai_provider)

        result = plugin.get_dependency("ai_provider")
        assert result is mock_ai_provider

    def test_get_dependency_default_callable(self):
        """Test getting a dependency with callable default."""
        plugin = ValidateIssuePlugin()

        mock_factory = Mock(return_value="created_value")
        result = plugin.get_dependency("non_existent", mock_factory)

        mock_factory.assert_called_once()
        assert result == "created_value"

    def test_get_dependency_default_value(self):
        """Test getting a dependency with static default."""
        plugin = ValidateIssuePlugin()

        result = plugin.get_dependency("non_existent", "default_value")
        assert result == "default_value"

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_execute_with_minimal_fields(self, mock_env_fetcher):
        """Test execution with minimal fields - edge case."""
        mock_env_fetcher.get.return_value = ""

        plugin = ValidateIssuePlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"fields": {}}  # Empty fields

        args = Namespace(issue_key="TEST-123", no_ai=True, no_cache=False)

        with patch("builtins.print") as mock_print:
            result = plugin.execute(mock_client, args)

        # Should have validation issues due to missing fields
        assert result is False
        print_calls = [call[0][0] for call in mock_print.call_args_list]
        assert any("❌ Validation failed for TEST-123" in str(call) for call in print_calls)

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_blocked_with_valid_reason(self, mock_env_fetcher):
        """Test validation for blocked issue with valid reason."""
        mock_env_fetcher.get.side_effect = lambda key, default="": {
            "JIRA_BLOCKED_FIELD": "customfield_10004",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10005",
        }.get(key, default)

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "To Do"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "task"},
            "customfield_10004": {"value": "True"},
            "customfield_10005": "Waiting for external dependency",
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Issue is blocked but has no reason" not in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_epic_type_does_not_need_epic_link(self, mock_env_fetcher):
        """Test that epics don't need to be linked to other epics."""
        mock_env_fetcher.get.side_effect = lambda key, default="": {"JIRA_EPIC_FIELD": "customfield_10001"}.get(
            key, default
        )

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "To Do"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "epic"},  # Epic type
            "customfield_10001": None,
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        # Epics should not be validated for epic links
        assert "Story is not linked to an epic" not in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_no_custom_fields_configured(self, mock_env_fetcher):
        """Test validation when no custom fields are configured."""
        mock_env_fetcher.get.return_value = ""  # No custom fields configured

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "story"},
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        # Should only have basic validations, no custom field validations
        assert len(issues) == 0  # No issues since required fields are present

    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_validate_with_ai_task_type(self, mock_env_fetcher, mock_get_ai_provider):
        """Test AI validation for task type issues."""
        mock_env_fetcher.get.return_value = ""
        mock_ai_provider = Mock()
        mock_get_ai_provider.return_value = mock_ai_provider

        plugin = ValidateIssuePlugin()

        fields = {"description": "Short task desc", "issuetype": {"name": "task"}}

        issues = plugin._validate_with_ai(fields, "TEST-1", "", False)
        # Tasks should also be validated
        assert "Description is too short (less than 50 characters)" in issues

    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_validate_with_ai_bug_type(self, mock_env_fetcher, mock_get_ai_provider):
        """Test AI validation for bug type issues."""
        mock_env_fetcher.get.return_value = ""
        mock_ai_provider = Mock()
        mock_get_ai_provider.return_value = mock_ai_provider

        plugin = ValidateIssuePlugin()

        fields = {
            "description": "Bug with a very detailed description that is more than 50 characters long",
            "issuetype": {"name": "bug"},
        }

        issues = plugin._validate_with_ai(fields, "TEST-1", "", False)
        # Should pass validation
        assert len(issues) == 0

    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_validate_with_ai_epic_type_skipped(self, mock_env_fetcher, mock_get_ai_provider):
        """Test that AI validation is skipped for epics."""
        mock_env_fetcher.get.return_value = ""
        mock_ai_provider = Mock()
        mock_get_ai_provider.return_value = mock_ai_provider

        plugin = ValidateIssuePlugin()

        fields = {
            "status": {"name": "To Do"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "epic"},
            "description": "Short",  # Would fail if validated
        }

        # AI validation should be skipped for epics
        issues = plugin._run_validations(fields, "TEST-1", False, False)
        assert "Description is too short" not in issues

    def test_rest_operation_with_invalid_key(self):
        """Test REST operation with missing issue key."""
        plugin = ValidateIssuePlugin()
        mock_client = Mock()

        with pytest.raises(KeyError):
            plugin.rest_operation(mock_client)  # Missing issue_key

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_story_with_valid_story_points(self, mock_env_fetcher):
        """Test that stories with valid story points pass validation."""
        mock_env_fetcher.get.side_effect = lambda key, default="": {"JIRA_STORY_POINTS_FIELD": "customfield_10003"}.get(
            key, default
        )

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "To Do"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "story"},
            "customfield_10003": "5",  # Has story points
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Story has no story points" not in issues

    @patch("jira_creator.plugins.validate_issue_plugin.EnvFetcher")
    def test_blocked_false_value(self, mock_env_fetcher):
        """Test validation for issue marked as not blocked."""
        mock_env_fetcher.get.side_effect = lambda key, default="": {
            "JIRA_BLOCKED_FIELD": "customfield_10004",
            "JIRA_BLOCKED_REASON_FIELD": "customfield_10005",
        }.get(key, default)

        plugin = ValidateIssuePlugin()
        fields = {
            "status": {"name": "To Do"},
            "assignee": {"displayName": "User"},
            "priority": {"name": "High"},
            "issuetype": {"name": "task"},
            "customfield_10004": {"value": "False"},  # Not blocked
            "customfield_10005": "",  # No reason needed
        }

        issues = plugin._run_validations(fields, "TEST-1", True, False)
        assert "Issue is blocked but has no reason" not in issues
