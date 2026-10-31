"""Tests for the JIRA_COMPONENT_NAME fallback in list-issues JQL building."""

from argparse import Namespace
from unittest.mock import Mock, patch

from jira_creator.plugins.list_issues_plugin import ListIssuesPlugin


def _args(component=None):
    return Namespace(
        project="TEST",
        component=component,
        status=None,
        assignee=None,
        reporter=None,
        summary=None,
        blocked=False,
        unblocked=False,
        sort="key",
        max_results=10,
    )


def _env(values):
    return lambda name, default=None: values.get(name, default)


def _jql_for(args):
    """Run the public execute() path and return the JQL handed to rest_operation."""
    plugin = ListIssuesPlugin()
    with patch.object(plugin, "rest_operation", return_value=[]) as rest:
        assert plugin.execute(Mock(), args) is True
    return rest.call_args.kwargs["jql"]


@patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
def test_env_component_used_when_flag_absent(mock_env):
    """JIRA_COMPONENT_NAME applies when --component is not given."""
    mock_env.get.side_effect = _env({"JIRA_COMPONENT_NAME": "Backend"})
    assert _jql_for(_args()).startswith("project = TEST AND component = 'Backend'")


@patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
def test_cli_component_wins_over_env(mock_env):
    """--component overrides JIRA_COMPONENT_NAME."""
    mock_env.get.side_effect = _env({"JIRA_COMPONENT_NAME": "Backend"})
    jql = _jql_for(_args("Frontend"))
    assert "component = 'Frontend'" in jql
    assert "Backend" not in jql


@patch("jira_creator.plugins.list_issues_plugin.EnvFetcher")
def test_no_component_filter_when_neither_set(mock_env):
    """No component condition when neither the flag nor the env var is set."""
    mock_env.get.side_effect = _env({})
    assert "component" not in _jql_for(_args())
