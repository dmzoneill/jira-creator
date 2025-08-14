#!/usr/bin/env python
"""Test for the final missing branch in view_helpers.py."""

from unittest.mock import Mock

from jira_creator.core.view_helpers import format_and_print_rows


class TestViewHelpersFinalBranch:
    """Test for uncovered branch 172->175 in view_helpers.py."""

    def test_format_and_print_rows_real_field_name_falsy(self, capsys):
        """Test format_and_print_rows when get_field_name returns falsy value - covers 172->175."""
        headers = ["key", "customfield_10001"]  # Has customfield_ prefix
        rows = [("TEST-1", "value")]

        mock_client = Mock()
        # Return falsy value (empty string) to trigger the 172->175 branch
        mock_client.get_field_name.return_value = ""  # Falsy, so matched stays False

        format_and_print_rows(rows, headers, mock_client)

        # Should print the table and use original header when get_field_name returns falsy
        captured = capsys.readouterr()
        assert "TEST-1" in captured.out

        # Verify get_field_name was called with the customfield
        mock_client.get_field_name.assert_called_with("customfield_10001")

    def test_format_and_print_rows_real_field_name_none(self, capsys):
        """Test format_and_print_rows when get_field_name returns None - covers 172->175."""
        headers = ["key", "customfield_10002"]  # Has customfield_ prefix
        rows = [("TEST-1", "value")]

        mock_client = Mock()
        # Return None to trigger the 172->175 branch
        mock_client.get_field_name.return_value = None  # Falsy, so matched stays False

        format_and_print_rows(rows, headers, mock_client)

        # Should print the table and use original header when get_field_name returns None
        captured = capsys.readouterr()
        assert "TEST-1" in captured.out

        # Verify get_field_name was called with the customfield
        mock_client.get_field_name.assert_called_with("customfield_10002")
