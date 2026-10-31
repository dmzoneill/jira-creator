"""
Unit tests for lint plugin.

Issues are linted through the public execute() entry point; the AI provider is
injected through the plugin constructor and the AI hash cache lives under a
temporary HOME.
"""

import hashlib
import json
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import AiError, AiProviderError, JiraClientRequestError
from jira_creator.plugins.lint_plugin import LintError, LintPlugin

ENV = {
    "JIRA_EPIC_FIELD": "customfield_epic",
    "JIRA_SPRINT_FIELD": "customfield_sprint",
    "JIRA_STORY_POINTS_FIELD": "customfield_points",
    "JIRA_BLOCKED_FIELD": "customfield_blocked",
    "JIRA_BLOCKED_REASON_FIELD": "customfield_reason",
    "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_ac",
    "JIRA_AI_PROVIDER": "test-provider",
}

CLEAN_FIELDS = {
    "status": {"name": "In Progress"},
    "assignee": {"name": "testuser"},
    "priority": {"name": "High"},
    "issuetype": {"name": "Story"},
    "customfield_epic": "EPIC-1",
    "customfield_sprint": [{"name": "Sprint 1"}],
    "customfield_points": 5,
    "customfield_blocked": {"value": "False"},
}


def sha256(text):
    """SHA-256 hex digest, as stored in the AI hash cache."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture(name="home", autouse=True)
def fixture_home(tmp_path, monkeypatch):
    """Use a temporary HOME and the custom field mapping in ENV."""
    monkeypatch.setenv("HOME", str(tmp_path))
    with patch(
        "jira_creator.plugins.lint_plugin.EnvFetcher.get", side_effect=lambda key, default=None: ENV.get(key, default)
    ):
        yield tmp_path


def cache_file(home):
    """Path of the AI hash cache under the temporary HOME."""
    return home / ".config" / "rh-issue" / "ai-hashes.json"


def lint(capsys, fields, ai_provider=None, no_cache=False, **overrides):
    """Run `lint TEST-1` on an issue; return (result, reported problems)."""
    client = Mock()
    client.request.return_value = {"fields": {**fields, **overrides}}
    plugin = LintPlugin(ai_provider=ai_provider) if ai_provider else LintPlugin()
    args = Namespace(issue_key="TEST-1", no_ai=ai_provider is None, no_cache=no_cache)
    result = plugin.execute(client, args)
    out = capsys.readouterr().out
    return result, [line[3:] for line in out.splitlines() if line.startswith(" - ")]


class TestLintPluginBasics:
    """Plugin metadata, REST call and field extraction."""

    def test_command_name(self):
        """Test command name property."""
        assert LintPlugin().command_name == "lint"

    def test_help_text(self):
        """Test help text property."""
        assert "Lint a single Jira issue" in LintPlugin().help_text

    def test_register_arguments(self):
        """Test argument registration."""
        mock_parser = Mock()
        LintPlugin().register_arguments(mock_parser)
        assert mock_parser.add_argument.call_count >= 3  # issue_key, --no-ai, --no-cache

    def test_rest_operation_success(self):
        """Test successful REST operation."""
        client = Mock()
        client.request.return_value = {"fields": {"summary": "Test issue"}}

        result = LintPlugin().rest_operation(client, issue_key="TEST-123")

        client.request.assert_called_once_with("GET", "/rest/api/2/issue/TEST-123")
        assert result == {"fields": {"summary": "Test issue"}}

    def test_rest_operation_request_error(self):
        """A Jira request error is wrapped in LintError."""
        client = Mock()
        client.request.side_effect = JiraClientRequestError("404")
        with pytest.raises(LintError, match="API request failed for TEST-123"):
            LintPlugin().rest_operation(client, issue_key="TEST-123")

    @pytest.mark.parametrize("error", [KeyError("k"), TypeError("t"), ValueError("API Error")], ids=repr)
    def test_rest_operation_failure(self, error):
        """A malformed-payload error is wrapped in LintError."""
        client = Mock()
        client.request.side_effect = error
        with pytest.raises(LintError, match="Failed to fetch issue TEST-123"):
            LintPlugin().rest_operation(client, issue_key="TEST-123")

    def test_extract_issue_fields(self):
        """extract_issue_fields maps the configured custom fields."""
        fields = {
            **CLEAN_FIELDS,
            "key": "TEST-123",
            "customfield_blocked": {"value": "True"},
            "customfield_reason": "Waiting for external dependency",
        }
        extracted = LintPlugin.extract_issue_fields(fields)
        assert extracted == {
            "issue_key": "TEST-123",
            "status": "In Progress",
            "assignee": {"name": "testuser"},
            "epic_link": "EPIC-1",
            "sprint_field": [{"name": "Sprint 1"}],
            "priority": {"name": "High"},
            "story_points": 5,
            "blocked_value": "True",
            "blocked_reason": "Waiting for external dependency",
            "issue_type": "Story",
        }

    def test_execute_lint_error(self, capsys):
        """A failed fetch prints and re-raises a LintError."""
        client = Mock()
        client.request.side_effect = ValueError("API failed")
        args = Namespace(issue_key="TEST-1", no_ai=True, no_cache=False)
        with pytest.raises(LintError, match="❌ Failed to lint issue TEST-1: Failed to fetch issue TEST-1"):
            LintPlugin().execute(client, args)
        assert "❌ Failed to lint issue TEST-1" in capsys.readouterr().out


class TestLintRules:
    """Rule-based checks (no AI)."""

    def test_clean_issue_passes(self, capsys):
        """An issue meeting every rule passes and AI is not used."""
        with patch("jira_creator.plugins.lint_plugin.get_ai_provider") as mock_get_ai:
            client = Mock()
            client.request.return_value = {"fields": dict(CLEAN_FIELDS)}
            result = LintPlugin().execute(client, Namespace(issue_key="TEST-1", no_ai=True, no_cache=False))
        assert result is True
        assert "✅ TEST-1 passed all lint checks" in capsys.readouterr().out
        mock_get_ai.assert_not_called()

    def test_problems_are_listed(self, capsys):
        """Problems are printed under a header and execute returns False."""
        client = Mock()
        client.request.return_value = {"fields": {**CLEAN_FIELDS, "priority": None, "assignee": None}}
        result = LintPlugin().execute(client, Namespace(issue_key="TEST-1", no_ai=True, no_cache=False))
        out = capsys.readouterr().out
        assert result is False
        assert "⚠️ Lint issues found in TEST-1:" in out
        assert " - ❌ Issue is In Progress but unassigned" in out
        assert " - ❌ Priority not set" in out

    def test_in_progress_unassigned(self, capsys):
        """In Progress issues need an assignee."""
        assert lint(capsys, CLEAN_FIELDS, assignee=None)[1] == ["❌ Issue is In Progress but unassigned"]

    def test_missing_epic(self, capsys):
        """Stories outside New/Refinement need an epic."""
        assert lint(capsys, CLEAN_FIELDS, customfield_epic=None)[1] == ["❌ Issue has no assigned Epic"]

    def test_epic_not_needed_for_epics_or_new_stories(self, capsys):
        """Epics, and stories in New, do not need an epic link."""
        assert not lint(capsys, CLEAN_FIELDS, customfield_epic=None, issuetype={"name": "Epic"})[1]
        assert not lint(capsys, CLEAN_FIELDS, customfield_epic=None, status={"name": "New"})[1]

    def test_in_progress_without_sprint(self, capsys):
        """In Progress issues need a sprint."""
        problems = lint(capsys, CLEAN_FIELDS, customfield_sprint=None)[1]
        assert problems == ["❌ Issue is In Progress but not assigned to a Sprint"]

    def test_missing_priority(self, capsys):
        """Priority must be set."""
        assert lint(capsys, CLEAN_FIELDS, priority=None)[1] == ["❌ Priority not set"]

    def test_missing_story_points(self, capsys):
        """Story points are required except in Refinement/New."""
        assert lint(capsys, CLEAN_FIELDS, customfield_points=None)[1] == ["❌ Story points not assigned"]
        assert not lint(capsys, CLEAN_FIELDS, customfield_points=None, status={"name": "Refinement"})[1]

    def test_blocked_without_reason(self, capsys):
        """Blocked issues need a reason."""
        problems = lint(capsys, CLEAN_FIELDS, customfield_blocked={"value": "True"})[1]
        assert problems == ["❌ Issue is blocked but has no blocked reason"]

    def test_blocked_with_reason(self, capsys):
        """A blocked issue with a reason passes."""
        blocked = {"customfield_blocked": {"value": "True"}, "customfield_reason": "Waiting for external team"}
        assert lint(capsys, CLEAN_FIELDS, **blocked) == (True, [])


class TestAiChecks:
    """AI quality checks and the AI hash cache they use."""

    def test_ai_provider_from_config_when_not_injected(self, capsys):
        """Without an injected provider, get_ai_provider(JIRA_AI_PROVIDER) is used."""
        provider = Mock()
        provider.improve_text.return_value = "OK"
        with patch("jira_creator.plugins.lint_plugin.get_ai_provider", return_value=provider) as mock_get_ai:
            client = Mock()
            client.request.return_value = {"fields": {**CLEAN_FIELDS, "summary": "Good"}}
            assert LintPlugin().execute(client, Namespace(issue_key="TEST-1", no_ai=False, no_cache=True))
        mock_get_ai.assert_called_once_with("test-provider")
        provider.improve_text.assert_called_once()
        assert "passed all lint checks" in capsys.readouterr().out

    def test_field_not_ok_is_reported(self, capsys, home):
        """A non-OK review becomes a problem and is not cached."""
        provider = Mock()
        provider.improve_text.return_value = "Summary is too vague and needs more details\n"
        result, problems = lint(capsys, CLEAN_FIELDS, ai_provider=provider, summary="Bad summary")
        assert result is False
        assert problems == ["❌ Summary: Summary is too vague and needs more details"]
        assert json.loads(cache_file(home).read_text(encoding="utf-8")) == {"TEST-1": {}}

    def test_ok_fields_are_cached(self, capsys, home):
        """OK reviews store each field's hash in the cache file."""
        provider = Mock()
        provider.improve_text.return_value = "OK - this is fine"
        fields = {**CLEAN_FIELDS, "summary": "S", "description": "D", "customfield_ac": "AC"}
        assert lint(capsys, fields, ai_provider=provider) == (True, [])
        assert provider.improve_text.call_count == 3
        assert json.loads(cache_file(home).read_text(encoding="utf-8")) == {
            "TEST-1": {
                "summary_hash": sha256("S"),
                "description_hash": sha256("D"),
                "acceptance_criteria_hash": sha256("AC"),
            }
        }

    def test_cached_fields_are_not_rechecked(self, capsys, home):
        """Fields whose hash is cached are not sent to the AI again."""
        cache_file(home).parent.mkdir(parents=True)
        cached = {"summary_hash": sha256("S"), "acceptance_criteria_hash": sha256("AC")}
        cache_file(home).write_text(json.dumps({"TEST-1": cached}), encoding="utf-8")
        provider = Mock()
        provider.improve_text.return_value = "OK"
        fields = {**CLEAN_FIELDS, "summary": "S", "description": "D", "customfield_ac": "AC"}
        assert lint(capsys, fields, ai_provider=provider) == (True, [])
        provider.improve_text.assert_called_once()
        assert "D" in provider.improve_text.call_args[0]

    def test_no_cache_rechecks_and_does_not_write(self, capsys, home):
        """With --no-cache every field is reviewed and nothing is written."""
        provider = Mock()
        provider.improve_text.return_value = "OK"
        lint(capsys, CLEAN_FIELDS, ai_provider=provider, no_cache=True, summary="S", description="D")
        assert provider.improve_text.call_count == 2
        assert not cache_file(home).exists()

    @pytest.mark.parametrize(
        "error",
        [
            AiError("AI service unavailable"),
            AiProviderError("AI service unavailable"),
            TypeError("AI service unavailable"),
        ],
        ids=lambda e: type(e).__name__,
    )
    def test_ai_failure_is_reported(self, capsys, error):
        """An AI error becomes a problem for that field."""
        provider = Mock()
        provider.improve_text.side_effect = error
        problems = lint(capsys, CLEAN_FIELDS, ai_provider=provider, description="Test content")[1]
        assert problems == ["❌ Failed to validate Description with AI: AI service unavailable"]


class TestUnexpectedErrors:
    """Errors outside the handled set are no longer swallowed."""

    def test_rest_operation_propagates(self):
        """An unexpected fetch error is not wrapped."""
        client = Mock()
        client.request.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError, match="boom"):
            LintPlugin().rest_operation(client, issue_key="TEST-1")

    def test_ai_review_propagates(self, capsys):
        """An unexpected AI error is not turned into a lint problem."""
        provider = Mock()
        provider.improve_text.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError, match="boom"):
            lint(capsys, CLEAN_FIELDS, ai_provider=provider, description="Test content")


class TestAiCache:
    """load_and_cache_issue() and save_cache()."""

    def test_load_missing_cache(self):
        """No cache file gives empty results."""
        assert LintPlugin().load_and_cache_issue("TEST-1") == ({}, {})

    def test_load_existing_cache(self, home):
        """The whole cache and the issue's entry are returned."""
        existing = {"TEST-1": {"summary_hash": "abc123"}, "TEST-2": {"summary_hash": "def"}}
        cache_file(home).parent.mkdir(parents=True)
        cache_file(home).write_text(json.dumps(existing), encoding="utf-8")
        assert LintPlugin().load_and_cache_issue("TEST-1") == (existing, {"summary_hash": "abc123"})
        assert LintPlugin().load_and_cache_issue("NEW-1") == (existing, {})

    def test_load_malformed_cache(self, home):
        """A malformed cache file is treated as empty."""
        cache_file(home).parent.mkdir(parents=True)
        cache_file(home).write_text("invalid json", encoding="utf-8")
        assert LintPlugin().load_and_cache_issue("TEST-1") == ({}, {})

    def test_save_cache_creates_directory(self, home):
        """save_cache creates the cache directory and writes JSON."""
        data = {"TEST-1": {"summary_hash": "abc"}}
        LintPlugin().save_cache(data)
        assert json.loads(cache_file(home).read_text(encoding="utf-8")) == data

    def test_save_cache_write_error_is_ignored(self, home):
        """A cache that cannot be written is silently skipped."""
        cache_file(home).mkdir(parents=True)
        LintPlugin().save_cache({"TEST-1": {}})
        assert cache_file(home).is_dir()
