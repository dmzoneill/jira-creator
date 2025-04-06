from unittest.mock import MagicMock

# Shared dictionary for issue data
base_issue = {
    "key": "AAP-1",
    "fields": {
        "status": {"name": "In Progress"},
        "assignee": {"displayName": "Dino"},
        "priority": {"name": "High"},
        "customfield_12310243": 5,
        "customfield_12316543": True,
        "customfield_12310940": ["name=Spring, state=ACTIVE"],
        "summary": "Fix bugs",
    },
}

base_issue_2 = {
    "key": "AAP-2",
    "fields": {
        "status": {"name": "Done"},
        "assignee": {"displayName": "Alice"},
        "priority": {"name": "Low"},
        "customfield_12310243": 3,
        "customfield_12316543": False,
        "customfield_12310940": ["name=Summer, state=ACTIVE"],
        "summary": "Improve UX",
    },
}

# Helper function to return common setup with different params


def setup_cli_and_args(
    cli, blocked=None, unblocked=None, reporter=None, status=None, summary=None
):
    # Setup the Jira mock
    cli.jira = MagicMock()

    # Setup the issues (base_issue and base_issue_2 can be modified in each test)
    issues = [base_issue, base_issue_2]

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
    args, issues = setup_cli_and_args(cli)
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-1" in captured.out


def test_list_reporter_print(cli, capsys):
    # Modify summary for this test case
    summary = "Fix bugs" * 20  # Update summary for this test case
    args, issues = setup_cli_and_args(cli, summary=summary, reporter="John")
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-1" in captured.out


def test_list_with_filters(cli, capsys):
    args, issues = setup_cli_and_args(cli, status="In Progress")
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-1" in captured.out
    assert "AAP-2" not in captured.out


def test_list_with_blocked_filter(cli, capsys):
    args, issues = setup_cli_and_args(cli, blocked=True)
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-2" in captured.out
    assert "AAP-1" not in captured.out


def test_list_with_unblocked_filter(cli, capsys):
    args, issues = setup_cli_and_args(cli, unblocked=True)
    cli.jira.list_issues.return_value = issues
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-1" in captured.out
    assert "AAP-2" not in captured.out
