from jira_creator.rh_jira import JiraCLI
from unittest.mock import MagicMock


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

    args = type("Args", (), {"project": None, "component": None, "user": None})
    cli.list(args)

    captured = capsys.readouterr()
    assert "AAP-1" in captured.out
    assert "Fix bugs" in captured.out
