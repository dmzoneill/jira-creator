#!/usr/bin/env python
"""
Unit tests for lint plugin.
"""

import json
import os
import tempfile
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import LintError
from jira_creator.plugins.lint_plugin import LintPlugin


class TestLintPlugin:
    """Tests for the LintPlugin class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.plugin = LintPlugin()
        self.mock_client = Mock()
        self.mock_ai_provider = Mock()

    def test_command_name(self):
        """Test command name property."""
        assert self.plugin.command_name == "lint"

    def test_help_text(self):
        """Test help text property."""
        assert "Lint a single Jira issue" in self.plugin.help_text

    def test_register_arguments(self):
        """Test argument registration."""
        mock_parser = Mock()
        self.plugin.register_arguments(mock_parser)

        # Verify that add_argument was called with expected arguments
        assert mock_parser.add_argument.call_count >= 3  # issue_key, --no-ai, --no-cache

    def test_rest_operation_success(self):
        """Test successful REST operation."""
        # Mock client response
        expected_response = {
            "fields": {"summary": "Test issue", "status": {"name": "In Progress"}, "assignee": {"name": "testuser"}}
        }
        self.mock_client.request.return_value = expected_response

        # Call rest operation
        result = self.plugin.rest_operation(self.mock_client, issue_key="TEST-123")

        # Verify client was called correctly
        self.mock_client.request.assert_called_once_with("GET", "/rest/api/2/issue/TEST-123")
        assert result == expected_response

    def test_rest_operation_failure(self):
        """Test REST operation failure."""
        # Mock client to raise exception
        self.mock_client.request.side_effect = Exception("API Error")

        # Test that LintError is raised
        with pytest.raises(LintError, match="Failed to fetch issue TEST-123"):
            self.plugin.rest_operation(self.mock_client, issue_key="TEST-123")

    def test_validate_progress_success(self):
        """Test progress validation - success case."""
        problems = []
        self.plugin._validate_progress("In Progress", {"name": "testuser"}, problems)
        assert len(problems) == 0

    def test_validate_progress_failure(self):
        """Test progress validation - failure case."""
        problems = []
        self.plugin._validate_progress("In Progress", None, problems)
        assert len(problems) == 1
        assert "unassigned" in problems[0]

    def test_validate_epic_link_success(self):
        """Test epic link validation - success case."""
        problems = []
        self.plugin._validate_epic_link("Story", "In Progress", "EPIC-123", problems)
        assert len(problems) == 0

    def test_validate_epic_link_failure(self):
        """Test epic link validation - failure case."""
        problems = []
        self.plugin._validate_epic_link("Story", "In Progress", None, problems)
        assert len(problems) == 1
        assert "no assigned Epic" in problems[0]

    def test_validate_priority_success(self):
        """Test priority validation - success case."""
        problems = []
        self.plugin._validate_priority({"name": "High"}, problems)
        assert len(problems) == 0

    def test_validate_priority_failure(self):
        """Test priority validation - failure case."""
        problems = []
        self.plugin._validate_priority(None, problems)
        assert len(problems) == 1
        assert "Priority not set" in problems[0]

    @patch("jira_creator.plugins.lint_plugin.get_ai_provider")
    @patch("jira_creator.core.env_fetcher.EnvFetcher.get")
    def test_execute_success_without_ai(self, mock_env_get, mock_get_ai_provider):
        """Test successful execute without AI."""

        # Mock environment variables
        def env_side_effect(key, default=None):
            env_map = {
                "JIRA_EPIC_FIELD": "customfield_12345",
                "JIRA_SPRINT_FIELD": "customfield_67890",
                "JIRA_STORY_POINTS_FIELD": "customfield_11111",
                "JIRA_BLOCKED_FIELD": "customfield_22222",
                "JIRA_BLOCKED_REASON_FIELD": "customfield_33333",
                "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_44444",
            }
            return env_map.get(key, default)

        mock_env_get.side_effect = env_side_effect

        # Mock arguments
        args = Namespace(issue_key="TEST-123", no_ai=True, no_cache=False)

        # Mock client response - Epic type issue (exempt from epic validation)
        issue_response = {
            "fields": {
                "summary": "Test epic",
                "status": {"name": "Done"},
                "assignee": {"name": "testuser"},
                "priority": {"name": "High"},
                "issuetype": {"name": "Epic"},
                "customfield_12345": "EPIC-456",  # Epic field
                "customfield_67890": [{"name": "Sprint 1"}],  # Sprint field
                "customfield_11111": 5,  # Story points
                "customfield_22222": {"value": "False"},  # Not blocked
                "customfield_33333": "",  # No blocked reason needed
            }
        }
        self.mock_client.request.return_value = issue_response

        # Mock dependency injection
        self.plugin._injected_deps = {}

        # Execute
        result = self.plugin.execute(self.mock_client, args)

        # Verify result
        assert result is True
        mock_get_ai_provider.assert_not_called()

    def test_sha256(self):
        """Test SHA256 hash function."""
        text = "test text"
        hash_result = self.plugin._sha256(text)
        assert len(hash_result) == 64  # SHA256 produces 64-character hex string
        assert hash_result == self.plugin._sha256(text)  # Should be consistent

    @patch("os.path.exists")
    @patch("builtins.open")
    @patch("json.load")
    def test_load_cache_success(self, mock_json_load, mock_open, mock_exists):
        """Test successful cache loading."""
        mock_exists.return_value = True
        mock_json_load.return_value = {"TEST-123": {"summary_hash": "abc123"}}

        result = self.plugin._load_cache()

        assert result == {"TEST-123": {"summary_hash": "abc123"}}
        mock_open.assert_called_once()
        mock_json_load.assert_called_once()

    @patch("os.path.exists")
    def test_load_cache_no_file(self, mock_exists):
        """Test cache loading when file doesn't exist."""
        mock_exists.return_value = False

        result = self.plugin._load_cache()

        assert result == {}

    def test_load_and_cache_issue(self):
        """Test loading cache for specific issue."""
        # Mock _load_cache to return test data
        with patch.object(self.plugin, "_load_cache") as mock_load_cache:
            mock_load_cache.return_value = {"TEST-123": {"summary_hash": "abc123"}}

            cache, cached = self.plugin.load_and_cache_issue("TEST-123")

            assert cache == {"TEST-123": {"summary_hash": "abc123"}}
            assert cached == {"summary_hash": "abc123"}

    def test_load_and_cache_issue_new_issue(self):
        """Test loading cache for new issue."""
        # Mock _load_cache to return empty data
        with patch.object(self.plugin, "_load_cache") as mock_load_cache:
            mock_load_cache.return_value = {}

            cache, cached = self.plugin.load_and_cache_issue("NEW-123")

            assert cache == {}
            assert cached == {}

    @patch("jira_creator.plugins.lint_plugin.get_ai_provider")
    @patch("jira_creator.plugins.lint_plugin.EnvFetcher.get")
    def test_execute_with_ai_provider(self, mock_env_get, mock_get_ai_provider, capsys):
        """Test execute method with AI provider."""
        mock_env_get.return_value = "test_provider"
        mock_ai_provider = Mock()
        mock_get_ai_provider.return_value = mock_ai_provider

        plugin = LintPlugin()
        mock_client = Mock()

        # Mock rest_operation and validation
        with (
            patch.object(plugin, "rest_operation", return_value={"fields": {"key": "TEST-1"}}),
            patch.object(plugin, "_validate_issue", return_value=[]),
        ):
            args = Namespace(issue_key="TEST-1", no_ai=False, no_cache=False)
            result = plugin.execute(mock_client, args)

            assert result is True
            captured = capsys.readouterr()
            assert "✅ TEST-1 passed all lint checks" in captured.out

    def test_execute_with_lint_problems(self, capsys):
        """Test execute method when problems are found."""
        plugin = LintPlugin()
        mock_client = Mock()

        # Mock rest_operation and validation to return problems
        with (
            patch.object(plugin, "rest_operation", return_value={"fields": {"key": "TEST-1"}}),
            patch.object(plugin, "_validate_issue", return_value=["Missing assignee", "No epic link"]),
        ):
            args = Namespace(issue_key="TEST-1", no_ai=True, no_cache=False)
            result = plugin.execute(mock_client, args)

            assert result is False
            captured = capsys.readouterr()
            assert "⚠️ Lint issues found in TEST-1:" in captured.out
            assert " - Missing assignee" in captured.out
            assert " - No epic link" in captured.out

    def test_execute_with_lint_error(self, capsys):
        """Test execute method when LintError is raised."""
        plugin = LintPlugin()
        mock_client = Mock()

        # Mock rest_operation to raise LintError
        with patch.object(plugin, "rest_operation", side_effect=LintError("API failed")):
            args = Namespace(issue_key="TEST-1", no_ai=True, no_cache=False)

            with pytest.raises(LintError, match="❌ Failed to lint issue TEST-1: API failed"):
                plugin.execute(mock_client, args)

            captured = capsys.readouterr()
            assert "❌ Failed to lint issue TEST-1: API failed" in captured.out

    @patch("jira_creator.plugins.lint_plugin.EnvFetcher.get")
    def test_validate_issue_with_ai_provider(self, mock_env_get):
        """Test _validate_issue with AI provider."""
        mock_env_get.return_value = "test_field"
        mock_ai_provider = Mock()

        plugin = LintPlugin()

        # Mock cache operations
        with (
            patch.object(plugin, "load_and_cache_issue", return_value=({}, {"ai_quality": True})) as mock_load,
            patch.object(plugin, "save_cache") as mock_save,
            patch.object(plugin, "_validate_with_ai") as mock_ai_validate,
        ):
            fields = {
                "key": "TEST-1",
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "User"},
                "issuetype": {"name": "Story"},
                "priority": {"name": "High"},
            }

            plugin._validate_issue(fields, mock_ai_provider, False)

            # Verify AI validation was called
            mock_ai_validate.assert_called_once()
            mock_load.assert_called_once_with("TEST-1")
            mock_save.assert_called_once()

    @patch("jira_creator.plugins.lint_plugin.EnvFetcher.get")
    def test_validate_issue_with_ai_no_cache(self, mock_env_get):
        """Test _validate_issue with AI provider and no_cache=True."""
        mock_env_get.return_value = "test_field"
        mock_ai_provider = Mock()

        plugin = LintPlugin()

        # Mock cache operations
        with (
            patch.object(plugin, "load_and_cache_issue", return_value=({}, {"ai_quality": True})) as mock_load,
            patch.object(plugin, "save_cache") as mock_save,
            patch.object(plugin, "_validate_with_ai") as mock_ai_validate,
        ):
            fields = {
                "key": "TEST-1",
                "status": {"name": "Done"},
                "assignee": {"displayName": "User"},
                "issuetype": {"name": "Bug"},
                "priority": {"name": "Medium"},
            }

            plugin._validate_issue(fields, mock_ai_provider, True)

            # With no_cache=True, load_and_cache_issue should NOT be called
            mock_ai_validate.assert_called_once()
            mock_load.assert_not_called()  # Because no_cache=True skips loading
            mock_save.assert_not_called()  # Because no_cache=True skips saving

    def test_rest_operation_api_error(self):
        """Test rest_operation when API call fails."""
        plugin = LintPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = Exception("API Error")

        with pytest.raises(LintError, match="Failed to fetch issue TEST-1: API Error"):
            plugin.rest_operation(mock_client, issue_key="TEST-1")

    def test_validate_with_ai_quality_checks(self):
        """Test _validate_with_ai method."""
        plugin = LintPlugin()
        mock_ai_provider = Mock()

        fields = {"key": "TEST-1", "summary": "Test issue", "description": "Test description"}
        cached = {}
        problems = []

        # Mock the field validation method
        with patch.object(plugin, "_validate_field_with_ai") as mock_validate_field:
            plugin._validate_with_ai(fields, mock_ai_provider, cached, problems, False)

            # Should call validation for both summary and description
            assert mock_validate_field.call_count == 2

    def test_validate_with_ai_poor_quality(self):
        """Test _validate_with_ai when AI finds issues."""
        plugin = LintPlugin()
        mock_ai_provider = Mock()

        fields = {"key": "TEST-1", "summary": "bad", "description": "poor desc"}
        cached = {}
        problems = []

        # Mock the field validation to add problems
        def mock_validate_field(field_name, content, hash_val, ai_provider, cached, problems):
            problems.append(f"❌ {field_name} quality issue: Content needs improvement")

        with patch.object(plugin, "_validate_field_with_ai", side_effect=mock_validate_field):
            plugin._validate_with_ai(fields, mock_ai_provider, cached, problems, False)

            # Should add problems for poor quality
            assert len(problems) == 2
            assert "Summary quality issue" in problems[0]
            assert "Description quality issue" in problems[1]

    def test_validate_with_ai_cached_results(self):
        """Test _validate_with_ai using cached results."""
        plugin = LintPlugin()
        mock_ai_provider = Mock()

        fields = {"key": "TEST-1", "summary": "Test", "description": "Test desc"}

        # Pre-populate cache with matching hashes to avoid validation
        cached = {"summary_hash": plugin._sha256("Test"), "description_hash": plugin._sha256("Test desc")}
        problems = []

        with patch.object(plugin, "_validate_field_with_ai") as mock_validate_field:
            plugin._validate_with_ai(fields, mock_ai_provider, cached, problems, False)

            # Should not call validation due to matching hashes
            mock_validate_field.assert_not_called()

    def test_load_and_cache_issue_file_operations(self):
        """Test load_and_cache_issue file operations."""
        plugin = LintPlugin()

        # Test with non-existent cache file
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "non_existent_cache.json")

            with patch.object(plugin, "_get_cache_path", return_value=cache_file):
                cache, cached = plugin.load_and_cache_issue("TEST-1")

                assert cache == {}
                assert cached == {}

        # Test with existing cache file
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "existing_cache.json")

            # Create existing cache file
            existing_cache = {"TEST-1": {"ai_quality": True, "ai_description": False}, "TEST-2": {"ai_quality": False}}
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(existing_cache, f)

            with patch.object(plugin, "_get_cache_path", return_value=cache_file):
                cache, cached = plugin.load_and_cache_issue("TEST-1")

                assert cache == existing_cache
                assert cached == {"ai_quality": True, "ai_description": False}

        # Test with malformed cache file (should handle gracefully)
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "malformed_cache.json")

            # Create malformed cache file
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write("invalid json")

            with patch.object(plugin, "_get_cache_path", return_value=cache_file):
                cache, cached = plugin.load_and_cache_issue("TEST-1")

                assert cache == {}
                assert cached == {}

    def test_save_cache_file_operations(self):
        """Test save_cache file operations."""
        plugin = LintPlugin()

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = os.path.join(temp_dir, "test_cache.json")

            cache_data = {"TEST-1": {"ai_quality": True, "ai_description": True}, "TEST-2": {"ai_quality": False}}

            with patch.object(plugin, "_get_cache_path", return_value=cache_file):
                plugin.save_cache(cache_data)

                # Verify file was written correctly
                assert os.path.exists(cache_file)
                with open(cache_file, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
                assert saved_data == cache_data

    def test_comprehensive_field_extraction(self):
        """Test extract_issue_fields with comprehensive field data."""
        fields = {
            "key": "TEST-123",
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "John Doe"},
            "issuetype": {"name": "Story"},
            "priority": {"name": "High"},
            "summary": "Test issue summary",
            "description": "Test issue description",
        }

        # Mock environment variables for custom fields
        with patch("jira_creator.plugins.lint_plugin.EnvFetcher.get") as mock_env_get:
            mock_env_get.side_effect = lambda key: {
                "JIRA_EPIC_FIELD": "customfield_10001",
                "JIRA_SPRINT_FIELD": "customfield_10002",
                "JIRA_STORY_POINTS_FIELD": "customfield_10003",
                "JIRA_BLOCKED_FIELD": "customfield_10004",
                "JIRA_BLOCKED_REASON_FIELD": "customfield_10005",
            }.get(key, "")

            # Add custom field values to test
            fields.update(
                {
                    "customfield_10001": "EPIC-1",
                    "customfield_10002": "Sprint 1",
                    "customfield_10003": 5,
                    "customfield_10004": {"value": "True"},
                    "customfield_10005": "Waiting for external dependency",
                }
            )

            extracted = LintPlugin.extract_issue_fields(fields)

            assert extracted["issue_key"] == "TEST-123"
            assert extracted["status"] == "In Progress"
            assert extracted["assignee"]["displayName"] == "John Doe"
            assert extracted["epic_link"] == "EPIC-1"
            assert extracted["sprint_field"] == "Sprint 1"
            assert extracted["priority"]["name"] == "High"
            assert extracted["story_points"] == 5
            assert extracted["blocked_value"] == "True"
            assert extracted["blocked_reason"] == "Waiting for external dependency"
            assert extracted["issue_type"] == "Story"
