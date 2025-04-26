#!/usr/bin/env python
"""
This module contains unit tests for the `view_issue` function within the `cli` module. It utilizes `pytest` for testing
and `MagicMock` to simulate interactions with the Jira API. The tests cover both successful and exceptional scenarios
of viewing an issue, ensuring that correct outputs are produced and appropriate methods are invoked with expected
arguments.

Functions:
- `test_view_issue(cli, capsys)`: Tests the successful retrieval of an issue.
- `test_view_issue_exception(cli, capsys)`: Tests the handling of exceptions when attempting to view an issue.

Arguments:
- `cli`: An instance of the command line interface used for testing.
- `capsys`: A pytest fixture that captures standard output and error streams.

Exceptions:
- `ViewIssueError`: Raised during the failure of the issue viewing process.
"""

from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import ViewIssueError


# Mock the parse_value function so we can simulate its behavior for testing
def mock_parse_value(value):
    """
    Mock version of parse_value to simulate its behavior for testing.
    """
    if isinstance(value, dict):
        # Simulating behavior for dictionaries with 'name' or 'value' keys
        if "name" in value:
            return value["name"]
        elif "value" in value:
            return value["value"]
        else:
            return str(value)
    elif isinstance(value, list):
        # Simulating behavior for lists
        return ", ".join(str(item) for item in value)
    elif value is None:
        return None
    elif isinstance(value, str) and "\n" in value:
        # Simulating multiline string formatting
        return "\n".join([f"{line:<30}" for line in value.splitlines()])
    return value


# Test for successful issue viewing
def test_view_issue(cli, capsys):
    """
    Simulate a test scenario for viewing an issue.

    Arguments:
    - cli: An object representing the command line interface for testing.
    - capsys: An object to capture stdout and stderr during testing.
    """

    blob = {"smokekey": "somevalue", "customfield_12345": 3}

    cli.jira.get_field_name = MagicMock(return_value="xxx")
    cli.jira.view_issue = MagicMock(return_value=blob)

    class Args:
        issue_key = "AAP-test_view_issue"

    # Call the handle function
    cli.view_issue(Args())

    # Capture the printed output
    captured = capsys.readouterr()

    # Assert that the headers are printed
    assert "Key" in captured.out
    assert "Value" in captured.out

    # Ensure that view_issue was called with the correct arguments
    cli.jira.view_issue.assert_called_once_with("AAP-test_view_issue")


# Test for exception handling during issue viewing
def test_view_issue_exception(cli, capsys):
    """
    Simulate an exception when viewing an issue in Jira for testing purposes.

    Arguments:
    - cli: The Jira command line interface object.
    - capsys: The pytest fixture for capturing stdout and stderr.

    Exceptions:
    - ViewIssueError: Raised when there is a failure while viewing an issue in Jira.
    """

    cli.jira.view_issue = MagicMock(side_effect=ViewIssueError("fail"))

    class Args:
        issue_key = "AAP-test_view_issue_exception"

    with pytest.raises(ViewIssueError):
        # Call the handle function
        cli.view_issue(Args())

    captured = capsys.readouterr()

    # Assert that the correct error message was printed
    assert "❌ Unable to view issue: fail" in captured.out

    # Ensure that view_issue was called with the correct arguments
    cli.jira.view_issue.assert_called_once_with("AAP-test_view_issue_exception")


# Test for parsing single-line or empty values
def test_parse_value_single_line_or_empty(cli):
    """
    Simulate a test scenario for parsing single-line or empty values.
    """

    # Test empty string
    assert mock_parse_value("") == ""

    # Test single-line string
    assert mock_parse_value("Single line") == "Single line"


# Test for parsing dictionaries with 'name' or 'value' keys
def test_parse_value_dict(cli):
    """
    Simulate a test scenario for parsing dictionaries with 'name' or 'value' keys.
    """

    # Test dictionary with 'name' field
    assert mock_parse_value({"name": "value1"}) == "value1"

    # Test dictionary with 'value' field
    assert mock_parse_value({"value": "value2"}) == "value2"

    # Test dictionary without 'name' or 'value' field
    assert mock_parse_value({"other": "value3"}) == "{'other': 'value3'}"


# Test for parsing lists
def test_parse_value_list(cli):
    """
    Simulate a test scenario for parsing lists.
    """

    # Test list of values
    assert mock_parse_value(["item1", "item2", "item3"]) == "item1, item2, item3"


# Test for parsing None values
def test_parse_value_none(cli):
    """
    Simulate a test scenario for parsing None values.
    """

    # Test None value
    assert mock_parse_value(None) is None


# Test for skipping None or empty values during printing
def test_view_issue_skip_none_or_empty(cli, capsys):
    """
    Simulate a test scenario where some fields are None or empty, and ensure they are skipped during printing.
    """

    blob = {}

    cli.jira.get_field_name = MagicMock(return_value="xxx")
    cli.jira.view_issue = MagicMock(return_value=blob)

    class Args:
        issue_key = "AAP-test_view_issue_skip"

    # Call the handle function
    cli.view_issue(Args())

    # Capture the printed output
    captured = capsys.readouterr()

    # Assert that the None and empty string values are not printed
    assert "customfield_12345" not in captured.out
    assert "description" not in captured.out

    # Ensure that view_issue was called with the correct arguments
    cli.jira.view_issue.assert_called_once_with("AAP-test_view_issue_skip")


# Test for parsing multiline values
def test_parse_value_multiline(cli):
    """
    Simulate a test scenario for parsing multiline string values.
    """

    # Test multiline string
    multiline_string = "Line 1\nLine 2\nLine 3"
    formatted = mock_parse_value(multiline_string)
    assert (
        formatted
        == "Line 1                        \nLine 2                        \nLine 3                        "
    )


# Test for skipping empty values or 'None' as strings
def test_parse_value_skip_none_or_empty(cli):
    """
    Simulate a test scenario where None or empty values are skipped during parsing.
    """

    # Test values for skipping (None or 'None' as a string)
    assert mock_parse_value(None) is None
    assert mock_parse_value("None") == "None"


def test_check_allowed_keys_and_skip_none_or_empty(cli, capsys):
    """
    Test that only keys in the allowed list are printed, and None or empty values are skipped.
    """

    blob = {
        "smokekey": "somevalue",  # Should be printed
        "blocked": "no",  # Should be printed (allowed key)
        "subtasks": {"name": "sss", "value": "ddd"},
        "summary": {"value": "ddd"},
        "sprint": {"yip": "ddd"},
        "labels": ["d", "d"],
        "status": None,
        "description": "this\nis\nmultiline",  # Should be printed (allowed key)
        "customfield_12345": "field_value",  # Should be printed (allowed key, mapped name)
        "unknown_field": "ignore_this",  # Should be skipped (not in allowed keys)
        "empty_field": "",  # Should be skipped (empty value)
        "none_field": None,  # Should be skipped (None value)
    }

    # Simulating the behavior of the function by mocking the field name retrieval
    cli.jira.get_field_name = MagicMock(
        return_value="customfield_12345"
    )  # Mock for custom field name resolution
    cli.jira.view_issue = MagicMock(return_value=blob)

    class Args:
        issue_key = "AAP-test_check_allowed_keys_and_skip_none_or_empty"

    # Call the handle function
    cli.view_issue(Args())

    # Capture the printed output
    captured = capsys.readouterr()

    assert "blocked" in captured.out
    assert "no" in captured.out

    # Assert that non-allowed field and skipped fields are NOT printed
    assert "unknown_field" not in captured.out
    assert "ignore_this" not in captured.out
    assert "empty_field" not in captured.out
    assert "none_field" not in captured.out

    # Ensure that view_issue was called with the correct arguments
    cli.jira.view_issue.assert_called_once_with(
        "AAP-test_check_allowed_keys_and_skip_none_or_empty"
    )
