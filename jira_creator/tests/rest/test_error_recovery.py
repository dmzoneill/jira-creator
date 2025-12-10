#!/usr/bin/env python
"""
Unit tests for AI error recovery features in JiraClient.

This module tests the error analysis and auto-remediation capabilities:
- ErrorContext serialization
- FixProposal parsing
- AI error analysis (Phase 1)
- AI auto-fix with user consent (Phase 2)
- Codebase and payload fix application
- Retry logic after fix
- Graceful degradation when AI unavailable
"""

import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from jira_creator.exceptions.exceptions import JiraClientRequestError
from jira_creator.rest.client import ErrorContext, FileChange, FixProposal, JiraClient


class TestErrorContext:
    """Test ErrorContext dataclass functionality."""

    def test_error_context_serialization(self):
        """Test that ErrorContext can be serialized to JSON."""
        error_context = ErrorContext(
            http_method="POST",
            api_path="/rest/api/2/issue",
            full_url="https://jira.example.com/rest/api/2/issue",
            json_payload={"fields": {"summary": "Test"}},
            query_params={"expand": "fields"},
            status_code=400,
            response_body='{"errorMessages": ["Field missing"]}',
            response_headers={"Content-Type": "application/json"},
            jira_error_messages=["Field missing"],
            jira_field_errors={"customfield_12345": "Invalid field"},
            timestamp="2025-01-01T00:00:00",
            jira_url="https://jira.example.com",
            project_key="PROJ",
        )

        json_str = error_context.to_json()
        parsed = json.loads(json_str)

        assert parsed["http_method"] == "POST"
        assert parsed["status_code"] == 400
        assert parsed["jira_error_messages"] == ["Field missing"]
        assert parsed["jira_field_errors"]["customfield_12345"] == "Invalid field"


class TestAnalyzeErrorWithAI:
    """Test _analyze_error_with_ai() method."""

    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.core.env_fetcher.EnvFetcher.get")
    def test_analyze_error_success(self, mock_env_get, mock_get_provider):
        """Test successful AI error analysis."""
        client = JiraClient()

        # Mock environment and provider
        mock_env_get.side_effect = lambda key, default="": "openai" if key == "JIRA_AI_PROVIDER" else default
        mock_provider = MagicMock()
        mock_provider.analyze_error.return_value = "## Root Cause\nField is invalid"
        mock_get_provider.return_value = mock_provider

        error_context = ErrorContext(
            http_method="POST",
            api_path="/rest/api/2/issue",
            full_url="https://jira.example.com/rest/api/2/issue",
            json_payload={},
            query_params={},
            status_code=400,
            response_body="",
            response_headers={},
            jira_error_messages=[],
            jira_field_errors={},
            timestamp="2025-01-01T00:00:00",
            jira_url="https://jira.example.com",
            project_key="PROJ",
        )

        result = client._analyze_error_with_ai(error_context)
        assert result == "## Root Cause\nField is invalid"
        mock_provider.analyze_error.assert_called_once()

    @patch("jira_creator.core.env_fetcher.EnvFetcher.get")
    def test_analyze_error_no_provider_configured(self, mock_env_get):
        """Test graceful handling when AI provider not configured."""
        client = JiraClient()

        # No AI provider configured
        mock_env_get.return_value = ""

        error_context = ErrorContext(
            http_method="POST",
            api_path="/rest/api/2/issue",
            full_url="https://jira.example.com/rest/api/2/issue",
            json_payload={},
            query_params={},
            status_code=400,
            response_body="",
            response_headers={},
            jira_error_messages=[],
            jira_field_errors={},
            timestamp="2025-01-01T00:00:00",
            jira_url="https://jira.example.com",
            project_key="PROJ",
        )

        result = client._analyze_error_with_ai(error_context)
        assert result is None

    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.core.env_fetcher.EnvFetcher.get")
    def test_analyze_error_provider_failure(self, mock_env_get, mock_get_provider):
        """Test graceful handling when AI provider fails."""
        client = JiraClient()

        # Mock environment and provider that fails
        mock_env_get.side_effect = lambda key, default="": "openai" if key == "JIRA_AI_PROVIDER" else default
        mock_provider = MagicMock()
        mock_provider.analyze_error.side_effect = Exception("API error")
        mock_get_provider.return_value = mock_provider

        error_context = ErrorContext(
            http_method="POST",
            api_path="/rest/api/2/issue",
            full_url="https://jira.example.com/rest/api/2/issue",
            json_payload={},
            query_params={},
            status_code=400,
            response_body="",
            response_headers={},
            jira_error_messages=[],
            jira_field_errors={},
            timestamp="2025-01-01T00:00:00",
            jira_url="https://jira.example.com",
            project_key="PROJ",
        )

        # Should return None on failure, not raise exception
        result = client._analyze_error_with_ai(error_context)
        assert result is None


class TestAnalyzeAndFixError:
    """Test _analyze_and_fix_error() method."""

    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.core.env_fetcher.EnvFetcher.get")
    def test_analyze_and_fix_success(self, mock_env_get, mock_get_provider):
        """Test successful AI auto-fix proposal."""
        client = JiraClient()

        # Mock environment and provider
        mock_env_get.side_effect = lambda key, default="": "openai" if key == "JIRA_AI_PROVIDER" else default
        mock_provider = MagicMock()
        fix_json = json.dumps(
            {
                "analysis": "## Root Cause\nBad field ID",
                "fix_type": "codebase",
                "confidence": 0.95,
                "file_changes": [
                    {
                        "file_path": "/home/user/file.py",
                        "old_content": "old code",
                        "new_content": "new code",
                        "line_start": 10,
                        "line_end": 12,
                    }
                ],
                "payload_fix": None,
                "reasoning": "Field ID is incorrect",
            }
        )
        mock_provider.analyze_and_fix_error.return_value = fix_json
        mock_get_provider.return_value = mock_provider

        error_context = ErrorContext(
            http_method="POST",
            api_path="/rest/api/2/issue",
            full_url="https://jira.example.com/rest/api/2/issue",
            json_payload={},
            query_params={},
            status_code=400,
            response_body="",
            response_headers={},
            jira_error_messages=[],
            jira_field_errors={},
            timestamp="2025-01-01T00:00:00",
            jira_url="https://jira.example.com",
            project_key="PROJ",
        )

        result = client._analyze_and_fix_error(error_context)
        assert result is not None
        assert result.fix_type == "codebase"
        assert result.confidence == 0.95
        assert len(result.file_changes) == 1
        assert result.file_changes[0].file_path == "/home/user/file.py"

    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.core.env_fetcher.EnvFetcher.get")
    def test_analyze_and_fix_invalid_json(self, mock_env_get, mock_get_provider):
        """Test handling of invalid JSON from AI."""
        client = JiraClient()

        # Mock environment and provider returning invalid JSON
        mock_env_get.side_effect = lambda key, default="": "openai" if key == "JIRA_AI_PROVIDER" else default
        mock_provider = MagicMock()
        mock_provider.analyze_and_fix_error.return_value = "Not valid JSON"
        mock_get_provider.return_value = mock_provider

        error_context = ErrorContext(
            http_method="POST",
            api_path="/rest/api/2/issue",
            full_url="https://jira.example.com/rest/api/2/issue",
            json_payload={},
            query_params={},
            status_code=400,
            response_body="",
            response_headers={},
            jira_error_messages=[],
            jira_field_errors={},
            timestamp="2025-01-01T00:00:00",
            jira_url="https://jira.example.com",
            project_key="PROJ",
        )

        # Should return None on invalid JSON
        result = client._analyze_and_fix_error(error_context)
        assert result is None


class TestPromptUserForFix:
    """Test _prompt_user_for_fix() method."""

    @patch("builtins.input", return_value="y")
    def test_prompt_user_accepts_fix(self, mock_input):
        """Test user accepting the proposed fix."""
        client = JiraClient()

        fix_proposal = FixProposal(
            analysis="Test analysis",
            fix_type="codebase",
            confidence=0.9,
            file_changes=[FileChange("/tmp/file.py", "old", "new")],
            payload_fix=None,
            reasoning="Test",
        )

        result = client._prompt_user_for_fix(fix_proposal)
        assert result is True

    @patch("builtins.input", return_value="n")
    def test_prompt_user_rejects_fix(self, mock_input):
        """Test user rejecting the proposed fix."""
        client = JiraClient()

        fix_proposal = FixProposal(
            analysis="Test analysis",
            fix_type="codebase",
            confidence=0.9,
            file_changes=[FileChange("/tmp/file.py", "old", "new")],
            payload_fix=None,
            reasoning="Test",
        )

        result = client._prompt_user_for_fix(fix_proposal)
        assert result is False

    @patch("jira_creator.rest.client.JiraClient._show_diff")
    @patch("builtins.input")
    def test_prompt_user_shows_diff_then_accepts(self, mock_input, mock_show_diff):
        """Test user requesting diff then accepting."""
        client = JiraClient()

        # First return 'd' (show diff), then 'y' (accept)
        mock_input.side_effect = ["d", "y"]

        fix_proposal = FixProposal(
            analysis="Test analysis",
            fix_type="codebase",
            confidence=0.9,
            file_changes=[FileChange("/tmp/file.py", "old", "new")],
            payload_fix=None,
            reasoning="Test",
        )

        result = client._prompt_user_for_fix(fix_proposal)
        assert result is True
        mock_show_diff.assert_called_once()


class TestApplyFix:
    """Test _apply_fix() method."""

    @patch("builtins.open", new_callable=mock_open, read_data="old code\n")
    @patch("os.path.exists", return_value=True)
    def test_apply_codebase_fix_success(self, mock_exists, mock_file):
        """Test successful application of codebase fix."""
        client = JiraClient()

        fix_proposal = FixProposal(
            analysis="Test",
            fix_type="codebase",
            confidence=0.9,
            file_changes=[FileChange("/tmp/file.py", "old code", "new code")],
            payload_fix=None,
            reasoning="Test",
        )

        result = client._apply_fix(fix_proposal)
        assert result is True
        mock_file.assert_called()

    @patch("builtins.open", new_callable=mock_open, read_data="old plugin code\n")
    @patch("os.path.exists", return_value=True)
    def test_apply_plugin_fix_with_reload(self, mock_exists, mock_file):
        """Test that plugins are automatically reloaded after fixing them."""
        # Create mock registry
        mock_registry = MagicMock()
        mock_registry.reload_plugin_from_file.return_value = True

        client = JiraClient(plugin_registry=mock_registry)

        fix_proposal = FixProposal(
            analysis="Test",
            fix_type="codebase",
            confidence=0.9,
            file_changes=[FileChange("/tmp/test_plugin.py", "old plugin code", "new plugin code")],
            payload_fix=None,
            reasoning="Test",
        )

        result = client._apply_fix(fix_proposal)
        assert result is True

        # Verify plugin was reloaded
        mock_registry.reload_plugin_from_file.assert_called_once_with("/tmp/test_plugin.py")

    def test_apply_payload_fix(self):
        """Test payload fix (doesn't modify files)."""
        client = JiraClient()

        fix_proposal = FixProposal(
            analysis="Test",
            fix_type="payload",
            confidence=0.9,
            file_changes=[],
            payload_fix={"fields": {"summary": "Fixed"}},
            reasoning="Test",
        )

        result = client._apply_fix(fix_proposal)
        assert result is True

    @patch("os.path.exists", return_value=False)
    def test_apply_fix_file_not_found(self, mock_exists):
        """Test handling when file to fix doesn't exist."""
        client = JiraClient()

        fix_proposal = FixProposal(
            analysis="Test",
            fix_type="codebase",
            confidence=0.9,
            file_changes=[FileChange("/nonexistent/file.py", "old", "new")],
            payload_fix=None,
            reasoning="Test",
        )

        result = client._apply_fix(fix_proposal)
        assert result is False


class TestShowDiff:
    """Test _show_diff() method."""

    @patch("builtins.print")
    def test_show_diff(self, mock_print):
        """Test diff display functionality."""
        client = JiraClient()

        old_content = "line 1\nline 2\nline 3"
        new_content = "line 1\nline 2 modified\nline 3"

        client._show_diff(old_content, new_content, "test.py")
        # Verify print was called (diff should be displayed)
        assert mock_print.called


class TestFullErrorRecoveryFlow:
    """Test complete error recovery flow with request() method."""

    @patch("jira_creator.rest.client.time.sleep")
    @patch("jira_creator.rest.client.requests.request")
    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.core.env_fetcher.EnvFetcher.get")
    def test_request_with_ai_analysis_on_failure(self, mock_env_get, mock_get_provider, mock_request, mock_sleep):
        """Test that AI analysis is triggered after request failures."""

        # Mock environment - provide defaults for all JiraClient __init__ needs
        def env_side_effect(key, default=""):
            env_vars = {
                "JIRA_URL": "https://jira.example.com",
                "JIRA_PROJECT_KEY": "PROJ",
                "JIRA_AFFECTS_VERSION": "",
                "JIRA_COMPONENT_NAME": "",
                "JIRA_PRIORITY": "Medium",
                "JIRA_JPAT": "fake-token",
                "JIRA_EPIC_FIELD": "customfield_10014",
                "JIRA_BOARD_ID": "123",
                "JIRA_AI_PROVIDER": "openai",
                "JIRA_AI_API_KEY": "fake-key",
                "JIRA_AI_MODEL": "gpt-4",
            }
            return env_vars.get(key, default)

        mock_env_get.side_effect = env_side_effect

        client = JiraClient()

        # Mock AI provider
        mock_provider = MagicMock()
        mock_provider.analyze_and_fix_error.return_value = json.dumps(
            {
                "analysis": "## Root Cause\nBad request",
                "fix_type": "none",
                "confidence": 0.8,
                "file_changes": [],
                "payload_fix": None,
                "reasoning": "Cannot fix automatically",
            }
        )
        mock_get_provider.return_value = mock_provider

        # Mock HTTP failure
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"errorMessages": ["Bad request"]}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_response

        # Should raise error after analysis
        with pytest.raises(JiraClientRequestError) as exc_info:
            client.request("POST", "/rest/api/2/issue", json_data={"test": "data"})

        # Verify AI analysis was called
        mock_provider.analyze_and_fix_error.assert_called_once()
        # Error message should include AI analysis
        assert "AI Analysis" in str(exc_info.value)

    @patch("jira_creator.rest.client.time.sleep")
    @patch("jira_creator.rest.client.requests.request")
    @patch("builtins.input", return_value="y")
    @patch("builtins.open", new_callable=mock_open, read_data="old code\n")
    @patch("os.path.exists", return_value=True)
    @patch("jira_creator.providers.get_ai_provider")
    @patch("jira_creator.core.env_fetcher.EnvFetcher.get")
    def test_request_with_successful_auto_fix_and_retry(
        self, mock_env_get, mock_get_provider, mock_exists, mock_file, mock_input, mock_request, mock_sleep
    ):
        """Test successful auto-fix and retry."""

        # Mock environment - provide defaults for all JiraClient __init__ needs
        def env_side_effect(key, default=""):
            env_vars = {
                "JIRA_URL": "https://jira.example.com",
                "JIRA_PROJECT_KEY": "PROJ",
                "JIRA_AFFECTS_VERSION": "",
                "JIRA_COMPONENT_NAME": "",
                "JIRA_PRIORITY": "Medium",
                "JIRA_JPAT": "fake-token",
                "JIRA_EPIC_FIELD": "customfield_10014",
                "JIRA_BOARD_ID": "123",
                "JIRA_AI_PROVIDER": "openai",
                "JIRA_AI_API_KEY": "fake-key",
                "JIRA_AI_MODEL": "gpt-4",
            }
            return env_vars.get(key, default)

        mock_env_get.side_effect = env_side_effect

        client = JiraClient()

        # Mock AI provider
        mock_provider = MagicMock()
        mock_provider.analyze_and_fix_error.return_value = json.dumps(
            {
                "analysis": "## Root Cause\nField incorrect",
                "fix_type": "codebase",
                "confidence": 0.95,
                "file_changes": [{"file_path": "/tmp/file.py", "old_content": "old code", "new_content": "new code"}],
                "payload_fix": None,
                "reasoning": "Fix field ID",
            }
        )
        mock_get_provider.return_value = mock_provider

        # First call fails (400), second call succeeds (200)
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 400
        mock_response_fail.text = '{"errorMessages": ["Bad field"]}'
        mock_response_fail.headers = {"Content-Type": "application/json"}

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.text = '{"key": "PROJ-123"}'
        mock_response_success.content = b'{"key": "PROJ-123"}'
        mock_response_success.json.return_value = {"key": "PROJ-123"}

        mock_request.side_effect = [
            mock_response_fail,  # Initial request fails
            mock_response_fail,  # Retry 1 fails
            mock_response_fail,  # Retry 2 fails
            mock_response_success,  # Retry after fix succeeds
        ]

        # Should succeed after applying fix
        result = client.request("POST", "/rest/api/2/issue", json_data={"test": "data"})
        assert result == {"key": "PROJ-123"}

    @patch("jira_creator.rest.client.time.sleep")
    @patch("jira_creator.rest.client.requests.request")
    @patch("jira_creator.core.env_fetcher.EnvFetcher.get")
    def test_request_without_ai_provider(self, mock_env_get, mock_request, mock_sleep):
        """Test request failure when no AI provider configured."""

        # Mock environment - NO AI provider configured
        def env_side_effect(key, default=""):
            env_vars = {
                "JIRA_URL": "https://jira.example.com",
                "JIRA_PROJECT_KEY": "PROJ",
                "JIRA_AFFECTS_VERSION": "",
                "JIRA_COMPONENT_NAME": "",
                "JIRA_PRIORITY": "Medium",
                "JIRA_JPAT": "fake-token",
                "JIRA_EPIC_FIELD": "customfield_10014",
                "JIRA_BOARD_ID": "123",
                "JIRA_AI_PROVIDER": "",  # No AI provider
            }
            return env_vars.get(key, default)

        mock_env_get.side_effect = env_side_effect

        client = JiraClient()

        # Mock HTTP failure
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"errorMessages": ["Bad request"]}'
        mock_response.headers = {"Content-Type": "application/json"}
        mock_request.return_value = mock_response

        # Should raise error without AI analysis (graceful degradation)
        with pytest.raises(JiraClientRequestError):
            client.request("POST", "/rest/api/2/issue", json_data={"test": "data"})
