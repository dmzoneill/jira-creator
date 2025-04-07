from unittest.mock import MagicMock

from core.env_fetcher import EnvFetcher

# Shared dictionary for issue data
base_issue = {
    "key": "AAP",
    "fields": {
        "status": {"name": "In Progress"},
        "assignee": {"displayName": "Dino"},
        "priority": {"name": "High"},
        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
        EnvFetcher.get("JIRA_BLOCKED_FIELD"): True,
        EnvFetcher.get("JIRA_SPRINT_FIELD"): ["name=Spring, state=ACTIVE"],
        "summary": "Fix bugs",
    },
}

base_issue_2 = {
    "key": "AAP",
    "fields": {
        "status": {"name": "Done"},
        "assignee": {"displayName": "Alice"},
        "priority": {"name": "Low"},
        EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 3,
        EnvFetcher.get("JIRA_BLOCKED_FIELD"): False,
        EnvFetcher.get("JIRA_SPRINT_FIELD"): ["name=Summer, state=ACTIVE"],
        "summary": "Improve UX",
    },
}

# Helper function to return common setup with different params


def setup_cli_and_args(
    cli,
    blocked=None,
    unblocked=None,
    reporter=None,
    status=None,
    summary=None,
    func=None,
):
    # Setup the Jira mock
    cli.jira = MagicMock()

    b1 = base_issue.copy()
    b2 = base_issue_2.copy()
    b1["key"] = b1["key"] + "-" + func + "-1"
    b2["key"] = b2["key"] + "-" + func + "-2"

    if blocked:
        print(b1)
        b1["fields"]["status"]["name"] = "In Progres"
        b2["fields"]["status"]["name"] = "In Progres"

    # Setup the issues (base_issue and base_issue_2 can be modified in each test)
    issues = [b1, b2]

    # Modify issues if required
    if summary:
        issues[0]["fields"]["summary"] = summary
    if reporter:
        issues[1]["fields"]["reporter"] = reporter
    if status:
        issues[0]["fields"]["status"]["name"] = status

    # Setup args with the passed filters
    args = type(
        "Args",
        (),
        {
            "project": None,
            "component": None,
            "assignee": None,
            "status": status,
            "summary": summary,
            "blocked": blocked,
            "unblocked": unblocked,
            "reporter": reporter,
        },
    )

    return args, issues


def test_list_print(cli, capsys):
    args, issues = setup_cli_and_args(cli, func="test_list_print")
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-test_list_print" in captured.out


def test_list_reporter_print(cli, capsys):
    # Modify summary for this test case
    summary = "Fix bugs" * 20  # Update summary for this test case
    args, issues = setup_cli_and_args(
        cli, summary=summary, reporter="John", func="test_list_reporter_print"
    )
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-test_list_reporter_print" in captured.out


def test_list_with_filters(cli, capsys):
    args, issues = setup_cli_and_args(
        cli, status="In Progress", func="test_list_with_filters"
    )
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-test_list_with_filters-1" in captured.out
    assert "AAP-test_list_with_filters-2" not in captured.out


def test_list_with_blocked_filter(cli, capsys):
    args, issues = setup_cli_and_args(
        cli, blocked=True, func="test_list_with_blocked_filter"
    )
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-test_list_with_blocked_filter-1" in captured.out
    assert "AAP-test_list_with_blocked_filter-2" in captured.out


def test_list_with_unblocked_filter(cli, capsys):
    args, issues = setup_cli_and_args(
        cli, unblocked=True, func="test_list_with_unblocked_filter"
    )
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-test_list_with_unblocked_filter-1" in captured.out
    assert "AAP-test_list_with_unblocked_filter-2" not in captured.out
