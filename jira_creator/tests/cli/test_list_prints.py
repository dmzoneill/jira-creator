from unittest.mock import MagicMock

from jira_creator.rh_jira import JiraCLI


def test_list_print(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    cli.jira.list_issues.return_value = [
        {
            "key": "AAP-1",
            "fields": {
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "Dino"},
                "priority": {"name": "High"},
                "customfield_12310243": 5,
                "customfield_12310940": ["name=Spring, state=ACTIVE"],
                "summary": "Fix bugs",
            },
        }
    ]

    # Properly mock args with all necessary attributes, including 'blocked'
    args = type(
        "Args",
        (),
        {
            "project": None,
            "component": None,
            "user": None,
            "status": None,
            "summary": None,
            "blocked": None,  # Add 'blocked' attribute
            "unblocked": None,  # Add 'unblocked' attribute
        },
    )
    cli.list_issues(args)

    captured = capsys.readouterr()
    assert "AAP-1" in captured.out


def test_list_with_filters(capsys):
    cli = JiraCLI()
    cli.jira = MagicMock()

    # Mock list_issues to return a list of issues
    cli.jira.list_issues.return_value = [
        {
            "key": "AAP-1",
            "fields": {
                "status": {"name": "In Progress"},
                "assignee": {"displayName": "Dino"},
                "priority": {"name": "High"},
                "customfield_12310243": 5,
                "customfield_12310940": ["name=Spring, state=ACTIVE"],
                "summary": "Fix bugs",
            },
        },
        {
            "key": "AAP-2",
            "fields": {
                "status": {"name": "Done"},
                "assignee": {"displayName": "Alice"},
                "priority": {"name": "Low"},
                "customfield_12310243": 3,
                "customfield_12310940": ["name=Summer, state=ACTIVE"],
                "summary": "Improve UX",
            },
        },
    ]

    # Mock the args with filters applied
    args = type(
        "Args",
        (),
        {
            "project": None,
            "component": None,
            "user": None,
            "status": "In Progress",  # Only 'In Progress' issues should be shown
            "summary": None,
            "blocked": None,
            "unblocked": None,
        },
    )

    # Run the list method with the filters
    cli.list_issues(args)

    captured = capsys.readouterr()

    # Ensure only the "AAP-1" issue is printed (the one with status "In Progress")
    assert "AAP-1" in captured.out
    assert (
        "AAP-2" not in captured.out
    )  # "AAP-2" should be skipped because its status is "Done"
