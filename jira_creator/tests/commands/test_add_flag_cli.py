from unittest.mock import MagicMock


def test_add_flag(cli, capsys):
    # Mock the jira method
    cli.jira.add_flag = MagicMock(return_value={"status": "success"})

    class Args:
        issue_key = "AAP-test_add_flag"

    response = cli.add_flag(Args())

    # Capture output and assert
    out, err = capsys.readouterr()
    assert "success" in response["status"]
    cli.jira.add_flag.assert_called_once_with("AAP-test_add_flag")
