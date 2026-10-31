#!/usr/bin/env python
"""CLI argument parsing tests for set-workstream (issue #37)."""

from argparse import ArgumentParser
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import MissingConfigVariable
from jira_creator.plugins.set_workstream_plugin import SetWorkstreamError, SetWorkstreamPlugin


def _parser():
    parser = ArgumentParser(exit_on_error=False)
    SetWorkstreamPlugin().register_arguments(parser)
    return parser


def test_flag_only_parses():
    """--workstream-id alone no longer exits with a usage error."""
    args = _parser().parse_args(["AAP-1", "--workstream-id", "WS-9"])
    assert args.issue_key == "AAP-1"
    assert args.workstream_id == "WS-9"


def test_flag_before_issue_key_parses():
    """The optional positional must not overwrite the flag value."""
    args = _parser().parse_args(["--workstream-id", "WS-9", "AAP-1"])
    assert args.workstream_id == "WS-9"


def test_positional_still_works():
    """The positional form keeps working."""
    args = _parser().parse_args(["AAP-1", "WS-7"])
    assert args.workstream_id == "WS-7"


def test_neither_given_defaults_to_none():
    """With neither form, the value is None so the env default applies."""
    args = _parser().parse_args(["AAP-1"])
    assert args.workstream_id is None


def _fake_get(var_name):
    if var_name == "JIRA_WORKSTREAM_FIELD":
        return "customfield_1"
    raise MissingConfigVariable(var_name)


@patch("jira_creator.plugins.set_workstream_plugin.EnvFetcher")
def test_neither_given_and_no_default_errors_clearly(mock_env):
    """With no ID and no JIRA_WORKSTREAM_ID, a clear SetWorkstreamError is raised."""
    mock_env.get.side_effect = _fake_get
    args = _parser().parse_args(["AAP-1"])
    client = Mock()
    with pytest.raises(SetWorkstreamError, match="--workstream-id"):
        SetWorkstreamPlugin().execute(client, args)
    client.request.assert_not_called()


@patch("jira_creator.plugins.set_workstream_plugin.EnvFetcher")
def test_flag_value_sent_to_jira(mock_env):
    """The flag value reaches the REST payload."""
    mock_env.get.side_effect = _fake_get
    args = _parser().parse_args(["AAP-1", "--workstream-id", "WS-9"])
    client = Mock()
    assert SetWorkstreamPlugin().execute(client, args) is True
    client.request.assert_called_once_with(
        "PUT", "/rest/api/2/issue/AAP-1", json_data={"fields": {"customfield_1": [{"id": "WS-9"}]}}
    )
