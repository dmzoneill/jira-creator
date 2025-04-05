from unittest.mock import MagicMock


def test_add_comment_ai_fail(cli, capsys):
    # Mock the add_comment method
    cli.jira.add_comment = MagicMock()

    # Mock ai_provider's improve_text method to raise an exception
    ai_provider_mock = MagicMock()
    ai_provider_mock.improve_text.side_effect = Exception("fail")
    cli.ai_provider = ai_provider_mock

    class Args:
        issue_key = "AAP-1"
        text = "Comment text"

    # Call the method
    cli.add_comment(Args())

    # Capture output and assert
    out = capsys.readouterr().out
    assert "⚠️ AI cleanup failed" in out
