from unittest.mock import MagicMock, patch

import pytest
from core.env_fetcher import EnvFetcher

from jira_creator.core.view_helpers import (  # isort: skip
    clean_values,
    fetch_view_columns,
    filter_columns,
    flatten_fields,
    format_and_print_rows,
    get_sorted_columns,
    sort_rows,
    massage_issue_list,
)


# Mocking EnvFetcher for fetch_view_columns
@pytest.fixture
def mock_env_fetcher():
    with patch.object(EnvFetcher, "get") as mock_get:
        yield mock_get


def test_fetch_view_columns(mock_env_fetcher):
    # Test when JIRA_VIEW_COLUMNS is found and JIRA fields are replaced
    mock_env_fetcher.side_effect = lambda key: {
        "JIRA_VIEW_COLUMNS": "summary, JIRA_CUSTOM_FIELD",
        "JIRA_CUSTOM_FIELD": "Custom Field Value",
    }.get(key)

    result = fetch_view_columns()
    assert result == ["summary", "Custom Field Value"]

    # Test when the environment variable JIRA_VIEW_COLUMNS is not present
    mock_env_fetcher.side_effect = lambda key: {
        "JIRA_VIEW_COLUMNS": None,
    }.get(key)

    result = fetch_view_columns()
    assert result is None


# Test for get_sorted_columns


def test_get_sorted_columns():
    sort_string = "column1=asc,column2=desc"
    result = get_sorted_columns(sort_string)
    assert result == [("column1", "asc"), ("column2", "desc")]

    sort_string = "column1"
    result = get_sorted_columns(sort_string)
    assert result == [("column1", "asc")]


# Test for filter_columns


def test_filter_columns():
    issue = {"summary": "Test issue", "priority": "High"}
    view_columns = ["summary", "priority"]
    result = filter_columns(issue, view_columns)
    assert result == ["Test issue", "High"]

    view_columns = ["summary"]
    result = filter_columns(issue, view_columns)
    assert result == ["Test issue"]


# Test for sort_rows
def test_sort_rows():
    # Rows with tuples: ('column_name', 'value')
    rows = [("summary", "Task 1"), ("summary", "Task 3"), ("summary", "Task 2")]
    headers = ["summary"]  # Column name in the header
    sort_columns = [
        ("summary", "asc")
    ]  # Sorting in ascending order by the column 'summary'

    # Sort rows using the function
    result = sort_rows(rows, sort_columns, headers)

    # Correct sorted order (ascending by the second tuple element, i.e., task name)
    assert result == [
        ("summary", "Task 1"),
        ("summary", "Task 3"),
        ("summary", "Task 2"),
    ]


# Test for format_and_print_rows (this is more of a print/output test)
@patch("builtins.print")
def test_format_and_print_rows(mock_print, cli):
    # /* jscpd:ignore-start */
    rows = [
        {
            "key": "TEST-1",
            "issuetype": "story",
            "status": {"name": "To Do"},
            "assignee": {"displayName": "John Doe"},
            "reporter": {"displayName": "john Swan"},
            "priority": {"name": "High"},
            "summary": "Test issue 1",
            "sprint": "Sprint 1",
            "customfield_12310243": 5,
        },
        {
            "key": "TEST-2",
            "issuetype": "story",
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "Jane Smith"},
            "reporter": {"displayName": "Mike Swan"},
            "priority": {"name": "Medium"},
            "summary": "Test issue 2",
            "sprint": "Sprint 2",
            "customfield_12310243": 5,
        },
    ]
    # /* jscpd:ignore-end */
    headers = [
        "key",
        "issuetype",
        "status",
        "assignee",
        "reporter",
        "priority",
        "summary",
        "sprint",
        "customfield_12310243",
    ]

    cli.jira.get_field_name = MagicMock()
    cli.jira.get_field_name.return_value = "story points"

    format_and_print_rows(rows, headers, cli.jira)
    mock_print.assert_called()


def test_clean_values():
    rows = [(None, "data", 3.0), (None, "text", 4.5)]
    result = clean_values(rows)
    assert result == [("—", "data", "3"), ("—", "text", "4.5")]

    # Test with a long string value
    rows = [("short", "very long string that should be truncated")]
    result = clean_values(rows, max_length=10)
    assert result == [("short", "very long ")]


def test_missing_jira_view_column(mock_env_fetcher):
    # Test the case where the JIRA_VIEW_COLUMNS is missing or invalid
    mock_env_fetcher.side_effect = lambda key: {
        "JIRA_VIEW_COLUMNS": None,
    }.get(key)

    result = fetch_view_columns()
    assert result is None


def test_missing_environment_variable(mock_env_fetcher):
    # Test when an environment variable for a column is missing
    mock_env_fetcher.side_effect = lambda key: {
        "JIRA_VIEW_COLUMNS": "summary,JIRA_CUSTOM_FIELD",
        "JIRA_CUSTOM_FIELD": None,
    }.get(key)

    result = fetch_view_columns()
    assert result == ["summary", "JIRA_CUSTOM_FIELD"]
    mock_env_fetcher.assert_called_with("JIRA_CUSTOM_FIELD")


# Test for get_sorted_columns exception handling
def test_get_sorted_columns_invalid():
    sort_string = "column1=asc,column2=invalid_order"
    result = get_sorted_columns(sort_string)
    assert result == [("column1", "asc"), ("column2", "asc")]


# Test for sort_rows exception handling
def test_sort_rows_invalid_column():
    rows = [("summary", "Task 1"), ("summary", "Task 3")]
    headers = ["summary"]
    sort_columns = [("invalid_column", "asc")]

    result = sort_rows(rows, sort_columns, headers)
    assert result == [("summary", "Task 1"), ("summary", "Task 3")]


# Test for missing summary column handling
def test_format_and_print_rows_missing_summary(cli):
    # /* jscpd:ignore-start */
    rows = [
        {
            "key": "TEST-1",
            "issuetype": "story",
            "status": {"name": "To Do"},
            "assignee": {"displayName": "John Doe"},
            "reporter": {"displayName": "john Swan"},
            "priority": {"name": "High"},
            "summary": "Test issue 1",
            "sprint": "Sprint 1",
            "customfield_12310243": 5,
        },
        {
            "key": "TEST-2",
            "issuetype": "story",
            "status": {"name": "In Progress"},
            "assignee": {"displayName": "Jane Smith"},
            "reporter": {"displayName": "Mike Swan"},
            "priority": {"name": "Medium"},
            "summary": "Test issue 2",
            "sprint": "Sprint 2",
            "customfield_12310243": 5,
        },
    ]
    # /* jscpd:ignore-end */

    cli.jira.get_field_name = MagicMock()
    cli.jira.get_field_name.return_value = "story points"

    headers = [
        "key",
        "issuetype",
        "status",
        "assignee",
        "reporter",
        "priority",
        "summary",
        "sprint",
        "customfield_12310243",
    ]

    with patch("builtins.print") as mock_print:
        format_and_print_rows(rows, headers, cli.jira)  # Pass a mock JiraClient
        mock_print.assert_called()


# Test for appending placeholders
def test_clean_values_append_placeholders():
    rows = [
        (None, "data", 3.0),
        (None, "text", 4.5),
        (None, {"self": "", "value": "5"}, 4.5),
    ]
    result = clean_values(rows)
    assert result == [("—", "data", "3"), ("—", "text", "4.5"), ("—", "5", "4.5")]


# Test for truncating long summary field
def test_format_and_print_rows_truncate_summary():
    long_summary = "this is a very long summmary, will it get truncated is yet to be seen, lets try?"
    long_summary += long_summary
    long_summary += long_summary
    rows = [
        {
            "key": "TEST-1",
            "status": "To Do",
            "assignee": "John Doe",
            "summary": long_summary,
        },
        {
            "key": "TEST-2",
            "status": "In Progress",
            "assignee": "Jane Smith",
            "summary": "Test issue 2",
        },
        {
            "key": "TEST-2",
            "status": "To Do",
            "assignee": "Jane Smith",
            "summary": "A very long summary text that should be truncated",
        },
    ]
    headers = ["key", "status", "assignee", "summary"]

    with patch("builtins.print") as mock_print:
        format_and_print_rows(rows, headers, MagicMock())  # Pass a mock JiraClient
        mock_print.assert_called()
        # Ensure that long summaries are truncated
        assert (
            "A very long summary text that should be truncated"
            not in mock_print.call_args[0][0]
        )


# Test for defaulting to first issue keys in massage_issue_list when view_columns is not present
def test_massage_issue_list_default_view_columns():
    issues = [
        {"key": "TEST-1", "summary": "Issue summary", "status": {"name": "To Do"}}
    ]
    args = MagicMock(sort=None)  # No sort argument
    headers, rows = massage_issue_list(args, issues)

    assert headers == [
        "key",
        "issuetype",
        "status",
        "priority",
        "summary",
        "assignee",
        "reporter",
        "sprint",
        "customfield_12310243",
    ]
    assert rows == [("TEST-1", "To Do", "Issue summary")]


# Test for sorting rows when 'sort' is provided in args
def test_massage_issue_list_with_sort():
    issues = [
        {"key": "TEST-1", "summary": "Issue summary", "status": {"name": "To Do"}},
        {
            "key": "TEST-2",
            "summary": "Another issue",
            "status": {"name": "In Progress"},
        },
    ]
    args = MagicMock(sort="key=asc")  # Sort by 'key' in ascending order
    headers, rows = massage_issue_list(args, issues)

    assert headers == [
        "key",
        "issuetype",
        "status",
        "priority",
        "summary",
        "assignee",
        "reporter",
        "sprint",
        "customfield_12310243",
    ]
    assert len(rows) == 2


# Test for flatten_fields
def test_flatten_fields():
    issue = {"fields": {"customfield_100": "value"}}
    result = flatten_fields(issue)
    assert result == {"customfield_100": "value"}

    issue = {"no_fields": "data"}
    result = flatten_fields(issue)
    assert result == {"no_fields": "data"}
