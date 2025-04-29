from unittest.mock import MagicMock

import pytest
from exceptions.exceptions import SetComponentError


def test_cli_set_component_success(cli, capsys):
    class Args:
        issue_key = "AAP-123"
        component_name = "New Component"

    cli.jira.set_component = MagicMock(return_value={})

    cli.set_component(Args())

    out = capsys.readouterr().out
    assert "Component 'New Component' set for issue 'AAP-123'" in out


def test_cli_set_component_failure(cli, capsys):
    class Args:
        issue_key = "AAP-456"
        component_name = "Failing Component"

    cli.jira.set_component = MagicMock(
        side_effect=SetComponentError("Failed to set component")
    )

    with pytest.raises(SetComponentError):
        cli.set_component(Args())

    out = capsys.readouterr().out
    assert "❌ Failed to set component" in out
