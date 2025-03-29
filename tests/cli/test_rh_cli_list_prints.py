from rh_jira import JiraCLI
from unittest.mock import MagicMock


def test_list_print(monkeypatch, capsys):
    cli = JiraCLI()
    monkeypatch.setattr(
        cli.jira,
        "list_issues",
        lambda *a, **k: [
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
        ],
    )
    args = type("Args", (), {"project": None, "component": None, "user": None})
    cli.list(args)
    captured = capsys.readouterr()
    assert "AAP-1" in captured.out
    assert "Fix bugs" in captured.out
