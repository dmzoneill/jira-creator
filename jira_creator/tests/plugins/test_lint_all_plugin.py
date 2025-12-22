#!/usr/bin/env python
"""
Unit tests for lint-all plugin.
"""

from argparse import Namespace
from collections import OrderedDict
from unittest.mock import Mock, patch

import pytest

from jira_creator.plugins.lint_all_plugin import LintAllError, LintAllPlugin


class TestLintAllPlugin:
    """Tests for the LintAllPlugin class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.plugin = LintAllPlugin()
        self.mock_client = Mock()
        self.mock_ai_provider = Mock()

    def test_command_name(self):
        """Test command name property."""
        assert self.plugin.command_name == "lint-all"

    def test_help_text(self):
        """Test help text property."""
        assert "Lint multiple Jira issues" in self.plugin.help_text

    def test_register_arguments(self):
        """Test argument registration."""
        mock_parser = Mock()
        self.plugin.register_arguments(mock_parser)

        # Verify that add_argument was called with expected arguments
        assert mock_parser.add_argument.call_count >= 6  # project, component, reporter, assignee, no-ai, no-cache

    def test_rest_operation_with_list_issues(self):
        """Test REST operation when client has list_issues method."""
        # Mock client with list_issues method
        self.mock_client.list_issues = Mock()
        expected_issues = [
            {"key": "TEST-1", "fields": {"summary": "Issue 1"}},
            {"key": "TEST-2", "fields": {"summary": "Issue 2"}},
        ]
        self.mock_client.list_issues.return_value = expected_issues

        # Call rest operation
        result = self.plugin.rest_operation(self.mock_client, project="TEST", component="backend")

        # Verify client was called correctly
        self.mock_client.list_issues.assert_called_once_with(
            project="TEST", component="backend", reporter=None, assignee=None
        )
        assert result == expected_issues

    def test_rest_operation_fallback_to_jql(self):
        """Test REST operation fallback to JQL when no list_issues method."""
        # Mock client without list_issues method
        if hasattr(self.mock_client, "list_issues"):
            delattr(self.mock_client, "list_issues")

        expected_response = {
            "issues": [
                {"key": "TEST-1", "fields": {"summary": "Issue 1"}},
                {"key": "TEST-2", "fields": {"summary": "Issue 2"}},
            ]
        }
        self.mock_client.request.return_value = expected_response

        # Call rest operation
        result = self.plugin.rest_operation(self.mock_client, project="TEST")

        # Verify client was called with JQL
        expected_jql = "/rest/api/2/search?jql=project = TEST&maxResults=100"
        self.mock_client.request.assert_called_once_with("GET", expected_jql, timeout=30)
        assert result == expected_response["issues"]

    def test_rest_operation_failure(self):
        """Test REST operation failure."""
        # Mock client to raise exception
        if hasattr(self.mock_client, "list_issues"):
            delattr(self.mock_client, "list_issues")
        self.mock_client.request.side_effect = Exception("API Error")

        # Test that LintAllError is raised
        with pytest.raises(LintAllError, match="Failed to fetch issues"):
            self.plugin.rest_operation(self.mock_client, project="TEST")

    def test_validate_progress_with_status_success(self):
        """Test progress validation with status tracking - success case."""
        problems = []
        status_dict = {}
        self.plugin._validate_progress_with_status("In Progress", {"name": "testuser"}, problems, status_dict)

        assert len(problems) == 0
        assert status_dict["Progress"] is True

    def test_validate_progress_with_status_failure(self):
        """Test progress validation with status tracking - failure case."""
        problems = []
        status_dict = {}
        self.plugin._validate_progress_with_status("In Progress", None, problems, status_dict)

        assert len(problems) == 1
        assert "unassigned" in problems[0]
        assert status_dict["Progress"] is False

    def test_validate_epic_link_with_status_success(self):
        """Test epic link validation with status tracking - success case."""
        problems = []
        status_dict = {}
        self.plugin._validate_epic_link_with_status("Story", "In Progress", "EPIC-123", problems, status_dict)

        assert len(problems) == 0
        assert status_dict["Epic"] is True

    def test_validate_epic_link_with_status_failure(self):
        """Test epic link validation with status tracking - failure case."""
        problems = []
        status_dict = {}
        self.plugin._validate_epic_link_with_status("Story", "In Progress", None, problems, status_dict)

        assert len(problems) == 1
        assert "no assigned Epic" in problems[0]
        assert status_dict["Epic"] is False

    def test_print_status_table_empty(self):
        """Test printing status table with empty data."""
        # Should not crash with empty data
        self.plugin._print_status_table([])

    def test_print_status_table_with_data(self):
        """Test printing status table with data."""
        failure_statuses = [
            {"jira_issue_id": "TEST-1", "Progress": True, "Epic": False, "Priority": True},
            {"jira_issue_id": "TEST-2", "Progress": False, "Epic": True, "Priority": None},
        ]

        # Should not crash - just testing it doesn't raise exceptions
        # In a real test, we might capture stdout to verify output format
        self.plugin._print_status_table(failure_statuses)

    def test_display_results_all_pass(self):
        """Test display results when all issues pass."""
        failures = {}
        failure_statuses = [{"jira_issue_id": "TEST-1", "Progress": True}]

        result = self.plugin._display_results(failures, failure_statuses)
        assert result is True

    def test_display_results_with_failures(self):
        """Test display results when some issues fail."""
        failures = {"TEST-1": ("Test issue", ["❌ Some problem"])}
        failure_statuses = [{"jira_issue_id": "TEST-1", "Progress": False}]

        result = self.plugin._display_results(failures, failure_statuses)
        assert result is False

    @patch("jira_creator.plugins.lint_all_plugin.get_ai_provider")
    def test_execute_no_issues(self, mock_get_ai_provider):
        """Test execute when no issues are found."""
        # Mock arguments
        args = Namespace(
            project="TEST",
            component=None,
            reporter=None,
            assignee=None,
            no_ai=False,
            no_cache=False,
            ai_fix=False,
            interactive=False,
        )

        # Mock rest_operation to return empty list
        with patch.object(self.plugin, "rest_operation") as mock_rest_op:
            mock_rest_op.return_value = []

            result = self.plugin.execute(self.mock_client, args)

            assert result is True
            mock_rest_op.assert_called_once()

    def test_validate_ai_fields_with_status(self):
        """Test AI field validation with status tracking."""
        fields = {
            "summary": "This is a good summary with enough content",
            "description": "This is a detailed description with sufficient content to pass validation",
            "issuetype": {"name": "Story"},
        }

        status_dict = {}
        problems = []
        cached = {}

        self.plugin._validate_ai_fields_with_status(fields, self.mock_ai_provider, cached, problems, status_dict, False)

        # Check that status flags were set
        assert "Summary" in status_dict
        assert "Description" in status_dict
        assert status_dict["Summary"] is True  # Should pass with good content
        assert status_dict["Description"] is True  # Should pass with good content

    @patch("jira_creator.plugins.lint_all_plugin.get_ai_provider")
    @patch("jira_creator.plugins.lint_all_plugin.EnvFetcher.get")
    def test_lint_all_issues_with_problems(self, mock_env_get, mock_get_ai_provider, capsys):
        """Test _lint_all_issues method when issues have problems."""
        mock_env_get.return_value = "test_provider"
        mock_ai_provider = Mock()
        mock_get_ai_provider.return_value = mock_ai_provider

        plugin = LintAllPlugin()
        mock_client = Mock()

        # Mock full issue details
        mock_client.request.return_value = {
            "fields": {
                "summary": "Test issue with problems",
                "status": {"name": "In Progress"},
                "assignee": None,  # Missing assignee will trigger problem
                "issuetype": {"name": "Story"},
                "priority": {"name": "High"},
            }
        }

        # Create test issues
        issues = [{"key": "TEST-1"}, {"key": "TEST-2"}]

        # Mock validate_issue_with_status to return problems
        with patch.object(plugin, "_validate_issue_with_status") as mock_validate:
            mock_validate.side_effect = [
                (["Missing assignee"], OrderedDict([("has_assignee", False), ("has_epic", True)])),
                ([], OrderedDict([("has_assignee", True), ("has_epic", True)])),
            ]

            failures, failure_statuses = plugin._lint_all_issues(mock_client, issues, mock_ai_provider, False)

            # Verify failures tracked correctly
            assert "TEST-1" in failures
            assert "TEST-2" not in failures
            assert len(failure_statuses) == 2

            # Check console output (summary is empty string due to mock)
            captured = capsys.readouterr()
            assert "❌ TEST-1  failed lint checks" in captured.out
            assert "✅ TEST-2  passed" in captured.out

    @patch("jira_creator.plugins.lint_all_plugin.get_ai_provider")
    @patch("jira_creator.plugins.lint_all_plugin.EnvFetcher.get")
    def test_lint_all_issues_api_error(self, mock_env_get, mock_get_ai_provider, capsys):
        """Test _lint_all_issues when API request fails."""
        mock_env_get.return_value = "test_provider"
        mock_ai_provider = Mock()
        mock_get_ai_provider.return_value = mock_ai_provider

        plugin = LintAllPlugin()
        mock_client = Mock()

        # Mock API error
        mock_client.request.side_effect = Exception("API Error")

        issues = [{"key": "TEST-1"}]

        failures, failure_statuses = plugin._lint_all_issues(mock_client, issues, mock_ai_provider, False)

        # Should handle error gracefully
        assert len(failures) == 0
        assert len(failure_statuses) == 0

        captured = capsys.readouterr()
        assert "❌ Failed to fetch TEST-1: API Error" in captured.out

    @patch("jira_creator.plugins.lint_all_plugin.LintPlugin")
    def test_validate_issue_with_status_comprehensive(self, mock_lint_plugin_class):
        """Test _validate_issue_with_status method."""
        mock_lint_plugin = Mock()
        mock_lint_plugin_class.return_value = mock_lint_plugin
        mock_lint_plugin.load_and_cache_issue.return_value = ({}, {"ai_quality": True})
        mock_lint_plugin.save_cache = Mock()

        plugin = LintAllPlugin()
        mock_ai_provider = Mock()

        # Mock extract_issue_fields
        with (
            patch.object(LintAllPlugin, "_validate_progress_with_status") as mock_progress,
            patch.object(LintAllPlugin, "_validate_epic_link_with_status") as mock_epic,
            patch.object(LintAllPlugin, "_validate_sprint_with_status") as mock_sprint,
            patch.object(LintAllPlugin, "_validate_priority_with_status") as mock_priority,
            patch.object(LintAllPlugin, "_validate_story_points_with_status") as mock_story_points,
            patch.object(LintAllPlugin, "_validate_blocked_with_status") as mock_blocked,
            patch.object(LintAllPlugin, "_validate_ai_fields_with_status") as mock_ai,
            patch("jira_creator.plugins.lint_all_plugin.LintPlugin.extract_issue_fields") as mock_extract,
        ):
            mock_extract.return_value = {
                "issue_key": "TEST-1",
                "status": "In Progress",
                "assignee": "user1",
                "issue_type": "Story",
                "epic_link": "EPIC-1",
                "sprint_field": "Sprint 1",
                "priority": "High",
                "story_points": 5,
                "blocked_value": "False",
                "blocked_reason": None,
            }

            fields = {
                "key": "TEST-1",
                "summary": "Test issue",
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "User One"},
            }

            problems, status = plugin._validate_issue_with_status(fields, mock_ai_provider, False, mock_lint_plugin)

            # Verify all validation methods were called
            mock_progress.assert_called_once()
            mock_epic.assert_called_once()
            mock_sprint.assert_called_once()
            mock_priority.assert_called_once()
            mock_story_points.assert_called_once()
            mock_blocked.assert_called_once()
            mock_ai.assert_called_once()

            # Verify cache operations
            mock_lint_plugin.load_and_cache_issue.assert_called_once_with("TEST-1")
            mock_lint_plugin.save_cache.assert_called_once()

    def test_execute_successful_flow(self):
        """Test complete successful execution flow."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        # Mock the methods
        with (
            patch.object(plugin, "rest_operation", return_value=[{"key": "TEST-1"}]) as mock_rest,
            patch.object(plugin, "_lint_all_issues", return_value=({}, [])) as mock_lint,
            patch.object(plugin, "_display_results", return_value=True) as mock_display,
        ):
            args = Namespace(
                no_ai=True,
                no_cache=False,
                project="TEST",
                component=None,
                reporter=None,
                assignee=None,
                ai_fix=False,
                interactive=False,
            )
            result = plugin.execute(mock_client, args)

            assert result is True
            mock_rest.assert_called_once()
            mock_lint.assert_called_once()
            mock_display.assert_called_once()

    def test_rest_operation_no_filters_default_jql(self):
        """Test rest_operation with no filters uses default JQL."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        # Remove list_issues method to force fallback to JQL
        del mock_client.list_issues

        mock_client.request.return_value = {"issues": []}

        # Test with no filters
        plugin.rest_operation(mock_client)

        expected_path = "/rest/api/2/search?jql=assignee = currentUser() AND updated >= -30d&maxResults=100"
        mock_client.request.assert_called_with("GET", expected_path, timeout=30)

    def test_rest_operation_fallback_jql_filters(self):
        """Test rest_operation fallback JQL with all filters."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        # Remove list_issues method to force fallback to JQL
        del mock_client.list_issues

        # Mock the search response
        mock_client.request.return_value = {"issues": [{"key": "TEST-1", "fields": {"summary": "Test issue"}}]}

        # Test with component filter
        plugin.rest_operation(mock_client, project="TEST", component="Backend")

        expected_path = "/rest/api/2/search?jql=project = TEST AND component = 'Backend'&maxResults=100"
        mock_client.request.assert_called_with("GET", expected_path, timeout=30)

        # Test with reporter filter
        mock_client.reset_mock()
        plugin.rest_operation(mock_client, project="TEST", reporter="john.doe")

        expected_path = "/rest/api/2/search?jql=project = TEST AND reporter = 'john.doe'&maxResults=100"
        mock_client.request.assert_called_with("GET", expected_path, timeout=30)

        # Test with assignee filter
        mock_client.reset_mock()
        plugin.rest_operation(mock_client, project="TEST", assignee="jane.smith")

        expected_path = "/rest/api/2/search?jql=project = TEST AND assignee = 'jane.smith'&maxResults=100"
        mock_client.request.assert_called_with("GET", expected_path, timeout=30)

    def test_execute_lint_all_error_handling(self):
        """Test execute method error handling."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        # Mock rest_operation to raise exception
        with patch.object(plugin, "rest_operation", side_effect=LintAllError("API failed")):
            args = Namespace(
                no_ai=True,
                project=None,
                component=None,
                reporter=None,
                assignee=None,
                ai_fix=False,
                interactive=False,
                no_cache=False,
            )

            with pytest.raises(LintAllError, match="❌ Failed to lint issues: API failed"):
                plugin.execute(mock_client, args)

    def test_validate_sprint_with_status_methods(self):
        """Test sprint validation methods."""
        plugin = LintAllPlugin()
        problems = []
        status_dict = {}

        # Test In Progress without sprint
        plugin._validate_sprint_with_status("In Progress", None, problems, status_dict)
        assert "❌ Issue is In Progress but not assigned to a Sprint" in problems
        assert status_dict["Sprint"] is False

        # Test success case
        problems.clear()
        status_dict.clear()
        plugin._validate_sprint_with_status("In Progress", "Sprint 1", problems, status_dict)
        assert len(problems) == 0
        assert status_dict["Sprint"] is True

    def test_validate_priority_with_status_methods(self):
        """Test priority validation methods."""
        plugin = LintAllPlugin()
        problems = []
        status_dict = {}

        # Test missing priority
        plugin._validate_priority_with_status(None, problems, status_dict)
        assert "❌ Priority not set" in problems
        assert status_dict["Priority"] is False

        # Test success case
        problems.clear()
        status_dict.clear()
        plugin._validate_priority_with_status("High", problems, status_dict)
        assert len(problems) == 0
        assert status_dict["Priority"] is True

    def test_validate_story_points_with_status_methods(self):
        """Test story points validation methods."""
        plugin = LintAllPlugin()
        problems = []
        status_dict = {}

        # Test missing story points outside allowed statuses
        plugin._validate_story_points_with_status(None, "In Progress", problems, status_dict)
        assert "❌ Story points not assigned" in problems
        assert status_dict["Story P."] is False

        # Test success case
        problems.clear()
        status_dict.clear()
        plugin._validate_story_points_with_status(5, "In Progress", problems, status_dict)
        assert len(problems) == 0
        assert status_dict["Story P."] is True

        # Test allowed status without story points (should pass)
        problems.clear()
        status_dict.clear()
        plugin._validate_story_points_with_status(None, "Refinement", problems, status_dict)
        assert len(problems) == 0
        assert status_dict["Story P."] is True

    def test_validate_blocked_with_status_methods(self):
        """Test blocked validation methods."""
        plugin = LintAllPlugin()
        problems = []
        status_dict = {}

        # Test blocked without reason
        plugin._validate_blocked_with_status("True", None, problems, status_dict)
        assert "❌ Issue is blocked but has no blocked reason" in problems
        assert status_dict["Blocked"] is False

        # Test success case
        problems.clear()
        status_dict.clear()
        plugin._validate_blocked_with_status("True", "Waiting for external team", problems, status_dict)
        assert len(problems) == 0
        assert status_dict["Blocked"] is True

        # Test not blocked (should pass)
        problems.clear()
        status_dict.clear()
        plugin._validate_blocked_with_status("False", None, problems, status_dict)
        assert len(problems) == 0
        assert status_dict["Blocked"] is True

    @patch("builtins.print")
    def test_execute_interactive_without_ai_fix(self, mock_print):
        """Test that interactive mode requires ai_fix - covers lines 75-76."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        args = Namespace(
            project=None, component=None, reporter=None, assignee=None, ai_fix=False, interactive=True, no_cache=False
        )

        result = plugin.execute(mock_client, args)

        assert result is False
        assert any("--interactive requires --ai-fix" in str(call) for call in mock_print.call_args_list)

    @patch("builtins.print")
    @patch("jira_creator.plugins.lint_all_plugin.EnvFetcher.get")
    def test_execute_ai_fix_without_plugin_registry(self, mock_env, mock_print):
        """Test AI fix mode without plugin registry - covers lines 89-94."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        mock_env.return_value = None

        # Set AI provider dependency but not plugin registry
        mock_ai_provider = Mock()
        plugin.set_dependency("ai_provider", mock_ai_provider)

        args = Namespace(
            project=None,
            component=None,
            reporter=None,
            assignee=None,
            ai_fix=True,
            interactive=False,
            no_cache=False,
            no_ai=False,
        )

        result = plugin.execute(mock_client, args)

        assert result is False
        assert any("AI fix requires plugin registry" in str(call) for call in mock_print.call_args_list)

    @patch("builtins.print")
    @patch("jira_creator.plugins.lint_all_plugin.EnvFetcher.get")
    @patch("jira_creator.plugins.lint_all_plugin.AIExecutor")
    def test_execute_with_ai_fix_and_relint(self, mock_executor_class, mock_env, mock_print):
        """Test AI fix mode with re-linting - covers lines 110-115."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        mock_env.side_effect = lambda key, default=None: {
            "JIRA_EPIC_FIELD": "customfield_10001",
            "JIRA_SPRINT_FIELD": "customfield_10002",
            "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_10003",
            "JIRA_STORY_POINTS_FIELD": "customfield_10004",
        }.get(key, default)

        # Mock dependencies
        mock_ai_provider = Mock()
        mock_plugin_registry = Mock()
        plugin.set_dependency("ai_provider", mock_ai_provider)
        plugin.set_dependency("plugin_registry", mock_plugin_registry)

        # Mock AI executor
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor

        # Mock issues with failures
        mock_client.request.return_value = {
            "issues": [
                {
                    "key": "TEST-1",
                    "fields": {
                        "summary": "Test issue",
                        "status": {"name": "Open"},
                        "issuetype": {"name": "Story"},
                        "priority": None,  # Will fail lint
                        "customfield_10001": None,
                        "customfield_10002": None,
                        "customfield_10003": None,
                        "customfield_10004": None,
                    },
                }
            ]
        }

        args = Namespace(
            project=None,
            component=None,
            reporter=None,
            assignee=None,
            ai_fix=True,
            interactive=False,
            no_cache=True,
            no_ai=False,
        )

        # First call returns failures, second call (after fixes) returns no failures
        with patch.object(plugin, "_lint_all_issues") as mock_lint:
            mock_lint.side_effect = [
                ({"TEST-1": ("Test issue", ["Missing priority"])}, {"TEST-1": {}}),  # First lint: failure
                ({}, {}),  # Second lint: success
            ]

            with patch.object(plugin, "_apply_ai_fixes") as mock_apply_fixes:
                plugin.execute(mock_client, args)

                # Should have called _apply_ai_fixes
                mock_apply_fixes.assert_called_once()

        # Should have re-linted
        assert mock_lint.call_count == 2

    @patch("builtins.print")
    @patch("jira_creator.plugins.lint_all_plugin.logger")
    def test_apply_ai_fixes(self, mock_logger, mock_print):
        """Test _apply_ai_fixes method - covers lines 451-485."""
        plugin = LintAllPlugin()
        mock_client = Mock()
        mock_executor = Mock()

        # Mock issue context
        mock_client.request.return_value = {
            "fields": {
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
                "assignee": {"name": "testuser"},
            }
        }

        # Mock AI executor
        mock_executor.generate_fixes.return_value = [
            {"function": "set_priority", "args": {"issue_key": "TEST-1", "priority": "High"}, "action": "Set priority"}
        ]
        mock_executor.execute_fixes.return_value = (1, 0)  # 1 success, 0 failures

        failures = {"TEST-1": ("Test issue", ["Missing priority"])}

        with patch.object(plugin, "_get_active_sprint", return_value={"id": "123", "name": "Sprint 1"}):
            plugin._apply_ai_fixes(mock_client, failures, mock_executor, interactive=False)

        # Verify AI executor was called
        mock_executor.generate_fixes.assert_called_once()
        mock_executor.execute_fixes.assert_called_once()

    @patch("builtins.print")
    @patch("jira_creator.plugins.lint_all_plugin.logger")
    def test_apply_ai_fixes_no_fixes_generated(self, mock_logger, mock_print):
        """Test _apply_ai_fixes when no fixes are generated - covers line 470."""
        plugin = LintAllPlugin()
        mock_client = Mock()
        mock_executor = Mock()

        # Mock issue context
        mock_client.request.return_value = {
            "fields": {
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
                "assignee": {"name": "testuser"},
            }
        }

        # AI returns no fixes
        mock_executor.generate_fixes.return_value = []

        failures = {"TEST-1": ("Test issue", ["Complex problem"])}

        with patch.object(plugin, "_get_active_sprint", return_value=None):
            plugin._apply_ai_fixes(mock_client, failures, mock_executor, interactive=False)

        # Should print "No applicable fixes"
        assert any("No applicable fixes" in str(call) for call in mock_print.call_args_list)

    @patch("builtins.print")
    @patch("jira_creator.plugins.lint_all_plugin.logger")
    def test_apply_ai_fixes_exception(self, mock_logger, mock_print):
        """Test _apply_ai_fixes with exception - covers lines 480-483."""
        plugin = LintAllPlugin()
        mock_client = Mock()
        mock_executor = Mock()

        # Mock exception in generate_fixes
        mock_executor.generate_fixes.side_effect = Exception("AI error")

        # Mock context building
        mock_client.request.return_value = {
            "fields": {
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
                "assignee": {"name": "testuser"},
            }
        }

        failures = {"TEST-1": ("Test issue", ["Problem"])}

        with patch.object(plugin, "_get_active_sprint", return_value=None):
            plugin._apply_ai_fixes(mock_client, failures, mock_executor, interactive=False)

        # Should log error
        assert mock_logger.error.called

    @patch("jira_creator.plugins.lint_all_plugin.logger")
    def test_build_issue_context_success(self, mock_logger):
        """Test _build_issue_context with successful fetch - covers lines 498-522."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        # Mock issue response
        mock_client.request.return_value = {
            "fields": {
                "status": {"name": "In Progress"},
                "issuetype": {"name": "Story"},
                "assignee": {"name": "john.doe"},
            }
        }

        # Mock active sprint
        with patch.object(plugin, "_get_active_sprint", return_value={"id": "456", "name": "Sprint 2"}):
            context = plugin._build_issue_context(mock_client, "TEST-1")

        assert context is not None
        assert context["issue_status"] == "In Progress"
        assert context["issue_type"] == "Story"
        assert context["current_assignee"] == "john.doe"
        assert context["active_sprint_id"] == "456"
        assert context["active_sprint_name"] == "Sprint 2"

    @patch("jira_creator.plugins.lint_all_plugin.logger")
    def test_build_issue_context_no_active_sprint(self, mock_logger):
        """Test _build_issue_context without active sprint - covers lines 518-520."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        mock_client.request.return_value = {
            "fields": {"status": {"name": "Open"}, "issuetype": {"name": "Bug"}, "assignee": None}
        }

        # No active sprint
        with patch.object(plugin, "_get_active_sprint", return_value=None):
            context = plugin._build_issue_context(mock_client, "TEST-1")

        assert context is not None
        assert context["active_sprint_id"] is None
        assert context["active_sprint_name"] is None
        assert context["current_assignee"] == "Unassigned"

    @patch("jira_creator.plugins.lint_all_plugin.logger")
    def test_build_issue_context_exception(self, mock_logger):
        """Test _build_issue_context with exception - covers lines 524-526."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        # Request raises exception
        mock_client.request.side_effect = Exception("API error")

        context = plugin._build_issue_context(mock_client, "TEST-1")

        assert context is None
        assert mock_logger.error.called

    @patch("jira_creator.plugins.lint_all_plugin.EnvFetcher.get")
    @patch("jira_creator.plugins.lint_all_plugin.logger")
    def test_get_active_sprint_success(self, mock_logger, mock_env):
        """Test _get_active_sprint with successful fetch - covers lines 538-551."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        mock_env.return_value = "123"  # JIRA_BOARD_ID

        mock_client.request.return_value = {"values": [{"id": "789", "name": "Active Sprint", "state": "active"}]}

        sprint = plugin._get_active_sprint(mock_client)

        assert sprint is not None
        assert sprint["id"] == "789"
        assert sprint["name"] == "Active Sprint"

    @patch("jira_creator.plugins.lint_all_plugin.EnvFetcher.get")
    @patch("jira_creator.plugins.lint_all_plugin.logger")
    def test_get_active_sprint_no_board_id(self, mock_logger, mock_env):
        """Test _get_active_sprint without board ID - covers lines 540-542."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        mock_env.return_value = None  # No JIRA_BOARD_ID

        sprint = plugin._get_active_sprint(mock_client)

        assert sprint is None
        assert mock_logger.warning.called

    @patch("jira_creator.plugins.lint_all_plugin.EnvFetcher.get")
    @patch("jira_creator.plugins.lint_all_plugin.logger")
    def test_get_active_sprint_no_sprints(self, mock_logger, mock_env):
        """Test _get_active_sprint with no active sprints - covers line 553."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        mock_env.return_value = "123"
        mock_client.request.return_value = {"values": []}  # No sprints

        sprint = plugin._get_active_sprint(mock_client)

        assert sprint is None

    @patch("jira_creator.plugins.lint_all_plugin.EnvFetcher.get")
    @patch("jira_creator.plugins.lint_all_plugin.logger")
    def test_get_active_sprint_exception(self, mock_logger, mock_env):
        """Test _get_active_sprint with exception - covers lines 555-557."""
        plugin = LintAllPlugin()
        mock_client = Mock()

        mock_env.return_value = "123"
        mock_client.request.side_effect = Exception("API error")

        sprint = plugin._get_active_sprint(mock_client)

        assert sprint is None
        assert mock_logger.error.called

    @patch("builtins.print")
    @patch("jira_creator.plugins.lint_all_plugin.logger")
    def test_apply_ai_fixes_no_context(self, mock_logger, mock_print):
        """Test _apply_ai_fixes when context fetch fails - covers lines 461-463."""
        plugin = LintAllPlugin()
        mock_client = Mock()
        mock_executor = Mock()

        failures = {"TEST-1": ("Test issue", ["Problem"])}

        # Context building returns None
        with patch.object(plugin, "_build_issue_context", return_value=None):
            plugin._apply_ai_fixes(mock_client, failures, mock_executor, interactive=False)

        # Should print "Failed to fetch issue context"
        assert any("Failed to fetch issue context" in str(call) for call in mock_print.call_args_list)
        # Should not call AI executor
        mock_executor.generate_fixes.assert_not_called()
