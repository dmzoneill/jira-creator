"""
Unit tests for lint-all plugin.

Everything goes through the public execute() and rest_operation() entry
points against a fake Jira client. The AI provider and plugin registry are
injected through the plugin constructor, AIExecutor is patched at the module
boundary, and the AI hash cache lives under a temporary HOME.
"""

import json
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.plugins.lint_all_plugin import LintAllError, LintAllPlugin

ENV = {
    "JIRA_EPIC_FIELD": "customfield_epic",
    "JIRA_SPRINT_FIELD": "customfield_sprint",
    "JIRA_STORY_POINTS_FIELD": "customfield_points",
    "JIRA_BLOCKED_FIELD": "customfield_blocked",
    "JIRA_BLOCKED_REASON_FIELD": "customfield_reason",
    "JIRA_ACCEPTANCE_CRITERIA_FIELD": "customfield_ac",
    "JIRA_AI_PROVIDER": "test-provider",
}

CLEAN = {
    "summary": "A clear summary",
    "status": {"name": "In Progress"},
    "assignee": {"name": "testuser"},
    "priority": {"name": "High"},
    "issuetype": {"name": "Bug"},
    "customfield_epic": "EPIC-1",
    "customfield_sprint": [{"name": "Sprint 1"}],
    "customfield_points": 5,
    "customfield_blocked": {"value": "False"},
}

EXECUTOR = "jira_creator.plugins.lint_all_plugin.AIExecutor"


@pytest.fixture(name="env", autouse=True)
def fixture_env(tmp_path, monkeypatch):
    """Temporary HOME and a mutable copy of the custom field mapping."""
    monkeypatch.setenv("HOME", str(tmp_path))
    env = dict(ENV)
    with patch(
        "jira_creator.core.env_fetcher.EnvFetcher.get", side_effect=lambda key, default=None: env.get(key, default)
    ):
        yield env


class FakeJira:
    """Jira client serving search, issue and active-sprint requests."""

    def __init__(self, issues, sprints=None, broken=()):
        self.issues = issues
        self.sprints = sprints
        self.broken = set(broken)
        self.paths = []

    def request(self, method, path, **_kwargs):
        """Answer a GET like the Jira REST API."""
        assert method == "GET"
        self.paths.append(path)
        if path.startswith("/rest/api/2/search"):
            return {"issues": [{"key": k, "fields": {"summary": f.get("summary", "")}} for k, f in self.issues.items()]}
        if path.startswith("/rest/agile/"):
            if isinstance(self.sprints, Exception):
                raise self.sprints
            return {"values": self.sprints or []}
        key = path.rsplit("/", 1)[1]
        if key in self.broken:
            raise RuntimeError(f"cannot fetch {key}")
        return {"fields": dict(self.issues[key])}


def make_args(**overrides):
    """Namespace for `lint-all` with defaults (no AI, no fixes)."""
    values = {
        "project": None,
        "component": None,
        "reporter": None,
        "assignee": None,
        "no_ai": True,
        "no_cache": False,
        "ai_fix": False,
        "interactive": False,
    }
    values.update(overrides)
    return Namespace(**values)


def run(capsys, issues, plugin=None, **overrides):
    """Run lint-all over `issues`; return (result, printed output)."""
    result = (plugin or LintAllPlugin()).execute(FakeJira(issues), make_args(**overrides))
    return result, capsys.readouterr().out


def table_rows(out):
    """Status table as {column: value} dicts, one per issue."""
    lines = [line for line in out.splitlines() if line.startswith("|")]
    headers = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in lines[1:]]
    return [dict(zip(headers, row)) for row in rows]


class TestLintAllBasics:
    """Metadata, argument checks and fetching the issue list."""

    def test_command_name(self):
        """Test command name property."""
        assert LintAllPlugin().command_name == "lint-all"

    def test_help_text(self):
        """Test help text property."""
        assert "Lint multiple Jira issues" in LintAllPlugin().help_text

    def test_register_arguments(self):
        """Test argument registration."""
        mock_parser = Mock()
        LintAllPlugin().register_arguments(mock_parser)
        assert mock_parser.add_argument.call_count >= 6

    def test_interactive_requires_ai_fix(self, capsys):
        """--interactive without --ai-fix is rejected."""
        assert run(capsys, {}, interactive=True) == (False, "⚠️  --interactive requires --ai-fix\n")

    def test_no_issues(self, capsys):
        """An empty result set passes."""
        assert run(capsys, {}) == (True, "✅ No issues found to lint.\n")

    def test_rest_operation_with_list_issues(self):
        """Clients with list_issues() get the filters passed through."""
        client = Mock()
        client.list_issues.return_value = [{"key": "TEST-1"}]
        result = LintAllPlugin().rest_operation(client, project="TEST", component="backend")
        client.list_issues.assert_called_once_with(project="TEST", component="backend", reporter=None, assignee=None)
        assert result == [{"key": "TEST-1"}]

    @pytest.mark.parametrize(
        "filters, jql",
        [
            ({"project": "TEST"}, "project = TEST"),
            (
                {"project": "P", "component": "c", "reporter": "r", "assignee": "a"},
                "project = P AND component = 'c' AND reporter = 'r' AND assignee = 'a'",
            ),
            ({}, "assignee = currentUser() AND updated >= -30d"),
        ],
    )
    def test_rest_operation_jql(self, filters, jql):
        """Without list_issues(), filters become a JQL search."""
        client = Mock(spec=["request"])
        client.request.return_value = {"issues": [{"key": "TEST-1"}]}
        assert LintAllPlugin().rest_operation(client, **filters) == [{"key": "TEST-1"}]
        client.request.assert_called_once_with("GET", f"/rest/api/2/search?jql={jql}&maxResults=100", timeout=30)

    def test_fetch_failure(self, capsys):
        """A failed search raises LintAllError and prints it."""
        client = Mock(spec=["request"])
        client.request.side_effect = RuntimeError("API Error")
        with pytest.raises(LintAllError, match="❌ Failed to lint issues: Failed to fetch issues: API Error"):
            LintAllPlugin().execute(client, make_args())
        assert "❌ Failed to lint issues" in capsys.readouterr().out


class TestLintAllRules:
    """Rule checks, per-issue output and the status table."""

    def test_all_pass(self, capsys):
        """Clean issues pass and every status column is ✅."""
        result, out = run(capsys, {"T-2": CLEAN, "T-1": CLEAN})
        assert result is True
        assert "✅ T-1 A clear summary passed" in out
        assert "🎉 All issues passed lint checks!" in out
        rows = table_rows(out)
        assert [row["jira_issue_id"] for row in rows] == ["T-1", "T-2"]
        assert set(rows[0].values()) == {"T-1", "✅"}
        assert list(rows[0]) == ["jira_issue_id", "Blocked", "Epic", "Priority", "Progress", "Sprint", "Story P."]

    @pytest.mark.parametrize(
        "overrides, problem, column",
        [
            ({"assignee": None}, "❌ Issue is In Progress but unassigned", "Progress"),
            ({"customfield_epic": None}, "❌ Issue has no assigned Epic", "Epic"),
            ({"customfield_sprint": None}, "❌ Issue is In Progress but not assigned to a Sprint", "Sprint"),
            ({"priority": None}, "❌ Priority not set", "Priority"),
            ({"customfield_points": None}, "❌ Story points not assigned", "Story P."),
            ({"customfield_blocked": {"value": "True"}}, "❌ Issue is blocked but has no blocked reason", "Blocked"),
        ],
    )
    def test_rule_failure(self, capsys, overrides, problem, column):
        """Each rule reports its problem and marks its column ❌."""
        result, out = run(capsys, {"T-1": {**CLEAN, **overrides}})
        assert result is False
        assert "❌ T-1 A clear summary failed lint checks" in out
        assert "⚠️ Issues with lint problems:" in out
        assert "🔍 T-1 - A clear summary" in out
        assert [line[3:] for line in out.splitlines() if line.startswith(" - ")] == [problem]
        row = table_rows(out)[0]
        assert row[column] == "❌"
        assert sum(value == "❌" for value in row.values()) == 1

    @pytest.mark.parametrize(
        "overrides",
        [
            {"customfield_epic": None, "issuetype": {"name": "Epic"}},
            {"customfield_epic": None, "status": {"name": "New"}, "issuetype": {"name": "Story"}},
            {"customfield_points": None, "status": {"name": "Refinement"}},
            {"customfield_blocked": {"value": "True"}, "customfield_reason": "Waiting"},
        ],
    )
    def test_rule_exemptions(self, capsys, overrides):
        """Epics, early statuses and blocked-with-reason are not problems."""
        assert run(capsys, {"T-1": {**CLEAN, **overrides}})[0] is True

    def test_unfetchable_issue_is_skipped(self, capsys):
        """An issue that cannot be fetched is reported and left out."""
        client = FakeJira({"T-1": CLEAN, "T-2": CLEAN}, broken={"T-2"})
        assert LintAllPlugin().execute(client, make_args()) is True
        out = capsys.readouterr().out
        assert "❌ Failed to fetch T-2: cannot fetch T-2" in out
        assert [row["jira_issue_id"] for row in table_rows(out)] == ["T-1"]

    def test_ai_columns(self, capsys, env):
        """With AI enabled, summary/description/AC columns are added; AC only for stories."""
        assert env["JIRA_AI_PROVIDER"]
        issues = {
            "T-1": {**CLEAN, "description": "A description that is long enough"},
            "T-2": {**CLEAN, "summary": "short", "issuetype": {"name": "Story"}, "customfield_ac": "Given when then"},
        }
        result, out = run(capsys, issues, plugin=LintAllPlugin(ai_provider=Mock()), no_ai=False)
        assert result is True
        rows = {row["jira_issue_id"]: row for row in table_rows(out)}
        assert (rows["T-1"]["Summary"], rows["T-1"]["Description"], rows["T-1"]["Acceptance Criteria"]) == (
            "✅",
            "✅",
            "❎",
        )
        assert (rows["T-2"]["Summary"], rows["T-2"]["Description"], rows["T-2"]["Acceptance Criteria"]) == (
            "❌",
            "❌",
            "✅",
        )

    def test_ai_cache_written_unless_no_cache(self, capsys, tmp_path):
        """AI runs save the per-issue cache entry, except with --no-cache."""
        cache = tmp_path / ".config" / "rh-issue" / "ai-hashes.json"
        run(capsys, {"T-1": CLEAN}, plugin=LintAllPlugin(ai_provider=Mock()), no_ai=False, no_cache=True)
        assert not cache.exists()
        run(capsys, {"T-1": CLEAN}, plugin=LintAllPlugin(ai_provider=Mock()), no_ai=False)
        assert json.loads(cache.read_text(encoding="utf-8")) == {"T-1": {}}

    def test_ai_provider_from_config(self, capsys):
        """Without an injected provider, get_ai_provider(JIRA_AI_PROVIDER) is used."""
        with patch("jira_creator.plugins.lint_all_plugin.get_ai_provider") as mock_get_ai:
            run(capsys, {"T-1": CLEAN}, no_ai=False)
        mock_get_ai.assert_called_once_with("test-provider")


class TestLintAllAiFix:
    """--ai-fix: generating and applying fixes, then re-linting."""

    def test_requires_registry(self, capsys):
        """--ai-fix without a plugin registry is rejected."""
        plugin = LintAllPlugin(ai_provider=Mock())
        assert run(capsys, {"T-1": CLEAN}, plugin=plugin, ai_fix=True) == (
            False,
            "⚠️  AI fix requires plugin registry and AI provider\n",
        )

    def test_fixes_applied_and_relinted(self, capsys, env):
        """Fixes are generated with issue context, executed, then issues are re-linted."""
        env["JIRA_BOARD_ID"] = "42"
        provider, registry = Mock(), Mock()
        client = FakeJira({"T-1": {**CLEAN, "priority": None}}, sprints=[{"id": 7, "name": "Sprint 7"}])
        with patch(EXECUTOR) as executor_cls:
            executor = executor_cls.return_value
            executor.generate_fixes.return_value = ["set-priority T-1 High"]
            executor.execute_fixes.return_value = (1, 0)
            result = LintAllPlugin(ai_provider=provider, plugin_registry=registry).execute(
                client, make_args(ai_fix=True, interactive=True)
            )
        out = capsys.readouterr().out
        assert result is False  # the fake issue is unchanged, so it still fails after re-linting
        executor_cls.assert_called_once_with(client, registry, provider)
        executor.generate_fixes.assert_called_once_with(
            "T-1",
            ["❌ Priority not set"],
            {
                "issue_status": "In Progress",
                "issue_type": "Bug",
                "current_assignee": "testuser",
                "active_sprint_id": 7,
                "active_sprint_name": "Sprint 7",
            },
        )
        executor.execute_fixes.assert_called_once_with(["set-priority T-1 High"], True)
        assert "🤖 Attempting to fix 1 issues with lint problems..." in out
        assert "🔧 Generated 1 fix command(s)" in out
        assert "📊 Fix Summary: 1 succeeded, 0 failed" in out
        assert "🔄 Re-linting issues after fixes..." in out
        assert "/rest/agile/1.0/board/42/sprint?state=active" in client.paths

    @pytest.mark.parametrize(
        "sprints, board",
        [(None, "42"), ([], "42"), (RuntimeError("agile down"), "42"), ([{"id": 1, "name": "S"}], "")],
    )
    def test_context_without_active_sprint(self, capsys, env, sprints, board):
        """No board, no active sprint or a sprint lookup error gives no sprint in the context."""
        env["JIRA_BOARD_ID"] = board
        client = FakeJira(
            {"T-1": {**CLEAN, "assignee": None, "status": {"name": "To Do"}, "priority": None}}, sprints=sprints
        )
        with patch(EXECUTOR) as executor_cls:
            executor = executor_cls.return_value
            executor.generate_fixes.return_value = []
            LintAllPlugin(ai_provider=Mock(), plugin_registry=Mock()).execute(client, make_args(ai_fix=True))
        context = executor.generate_fixes.call_args[0][2]
        assert context["current_assignee"] == "Unassigned"
        assert (context["active_sprint_id"], context["active_sprint_name"]) == (None, None)
        assert "ℹ️  No applicable fixes found" in capsys.readouterr().out

    def test_fix_error_is_counted(self, capsys):
        """An error while fixing one issue is reported and counted as a failure."""
        with patch(EXECUTOR) as executor_cls:
            executor_cls.return_value.generate_fixes.side_effect = RuntimeError("AI down")
            plugin = LintAllPlugin(ai_provider=Mock(), plugin_registry=Mock())
            out = run(capsys, {"T-1": {**CLEAN, "priority": None}}, plugin=plugin, ai_fix=True)[1]
        assert "   ❌ Error: AI down" in out
        assert "📊 Fix Summary: 0 succeeded, 1 failed" in out

    def test_context_fetch_failure_skips_issue(self, capsys):
        """If the issue cannot be re-fetched for context, it is skipped."""
        calls = []
        client = FakeJira({"T-1": {**CLEAN, "priority": None}})
        original = client.request

        def request(method, path, **kwargs):
            calls.append(path)
            if path.endswith("/T-1") and len(calls) == 3:
                raise RuntimeError("gone")
            return original(method, path, **kwargs)

        client.request = request
        with patch(EXECUTOR) as executor_cls:
            LintAllPlugin(ai_provider=Mock(), plugin_registry=Mock()).execute(client, make_args(ai_fix=True))
        out = capsys.readouterr().out
        assert "⚠️  Failed to fetch issue context, skipping" in out
        executor_cls.return_value.generate_fixes.assert_not_called()
        assert "📊 Fix Summary: 0 succeeded, 0 failed" in out
