#!/usr/bin/env python
"""Tests for the add link plugin."""

from argparse import ArgumentParser, Namespace
from unittest.mock import Mock, patch

import pytest

from jira_creator.exceptions.exceptions import AddLinkError
from jira_creator.plugins.add_link_plugin import AddLinkPlugin


class TestAddLinkPlugin:
    """Test cases for AddLinkPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = AddLinkPlugin()
        assert plugin.command_name == "add-link"
        assert plugin.help_text == "Create an issue link between two Jira issues"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = AddLinkPlugin()
        mock_parser = Mock(spec=ArgumentParser)
        mock_group = Mock()
        mock_parser.add_mutually_exclusive_group.return_value = mock_group

        plugin.register_arguments(mock_parser)

        # Check that mutually exclusive group was created
        mock_parser.add_mutually_exclusive_group.assert_called_once_with(required=True)
        # Check that link type arguments were added
        assert mock_group.add_argument.call_count == 5

    def test_rest_operation_outward(self):
        """Test the REST operation for outward link."""
        plugin = AddLinkPlugin()
        mock_client = Mock()
        mock_response = {}
        mock_client.request.return_value = mock_response

        plugin.rest_operation(
            mock_client, source_key="TEST-1", target_key="TEST-2", link_type="Blocks", direction="outward"
        )

        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/rest/api/2/issueLink"
        payload = call_args[1]["json_data"]
        assert payload["type"]["name"] == "Blocks"
        assert payload["outwardIssue"]["key"] == "TEST-1"
        assert payload["inwardIssue"]["key"] == "TEST-2"

    def test_rest_operation_inward(self):
        """Test the REST operation for inward link."""
        plugin = AddLinkPlugin()
        mock_client = Mock()
        mock_response = {}
        mock_client.request.return_value = mock_response

        plugin.rest_operation(
            mock_client, source_key="TEST-1", target_key="TEST-2", link_type="Blocks", direction="inward"
        )

        mock_client.request.assert_called_once()
        payload = mock_client.request.call_args[1]["json_data"]
        assert payload["inwardIssue"]["key"] == "TEST-1"
        assert payload["outwardIssue"]["key"] == "TEST-2"

    def test_execute_blocks(self):
        """Test execution with --blocks flag."""
        plugin = AddLinkPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {}

        args = Namespace(
            issue_key="TEST-1",
            blocks="TEST-2",
            blocked_by=None,
            relates_to=None,
            duplicates=None,
            clones=None,
        )

        with patch("builtins.print"):
            result = plugin.execute(mock_client, args)

        assert result is True

    def test_execute_blocked_by(self):
        """Test execution with --blocked-by flag."""
        plugin = AddLinkPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {}

        args = Namespace(
            issue_key="TEST-1",
            blocks=None,
            blocked_by="TEST-2",
            relates_to=None,
            duplicates=None,
            clones=None,
        )

        with patch("builtins.print"):
            result = plugin.execute(mock_client, args)

        assert result is True

    def test_execute_relates_to(self):
        """Test execution with --relates-to flag."""
        plugin = AddLinkPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {}

        args = Namespace(
            issue_key="TEST-1",
            blocks=None,
            blocked_by=None,
            relates_to="TEST-2",
            duplicates=None,
            clones=None,
        )

        result = plugin.execute(mock_client, args)
        assert result is True

    def test_execute_duplicates(self):
        """Test execution with --duplicates flag."""
        plugin = AddLinkPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {}

        args = Namespace(
            issue_key="TEST-1",
            blocks=None,
            blocked_by=None,
            relates_to=None,
            duplicates="TEST-2",
            clones=None,
        )

        result = plugin.execute(mock_client, args)
        assert result is True

    def test_execute_clones(self):
        """Test execution with --clones flag."""
        plugin = AddLinkPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {}

        args = Namespace(
            issue_key="TEST-1", blocks=None, blocked_by=None, relates_to=None, duplicates=None, clones="TEST-2"
        )

        result = plugin.execute(mock_client, args)
        assert result is True

    def test_execute_with_error(self):
        """Test execution when link creation fails."""
        plugin = AddLinkPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = AddLinkError("API error")

        args = Namespace(
            issue_key="TEST-1", blocks="TEST-2", blocked_by=None, relates_to=None, duplicates=None, clones=None
        )

        with pytest.raises(AddLinkError):
            plugin.execute(mock_client, args)

    def test_get_link_config_all_types(self):
        """Test _get_link_config for all link types."""
        plugin = AddLinkPlugin()

        # Test blocks
        args = Namespace(blocks="TEST-2", blocked_by=None, relates_to=None, duplicates=None, clones=None)
        config = plugin._get_link_config(args)  # pylint: disable=protected-access
        assert config["link_type"] == "Blocks"
        assert config["target_key"] == "TEST-2"
        assert config["direction"] == "outward"

        # Test blocked-by
        args = Namespace(blocks=None, blocked_by="TEST-2", relates_to=None, duplicates=None, clones=None)
        config = plugin._get_link_config(args)  # pylint: disable=protected-access
        assert config["link_type"] == "Blocks"
        assert config["direction"] == "inward"

        # Test relates-to
        args = Namespace(blocks=None, blocked_by=None, relates_to="TEST-2", duplicates=None, clones=None)
        config = plugin._get_link_config(args)  # pylint: disable=protected-access
        assert config["link_type"] == "Relates"

        # Test duplicates
        args = Namespace(blocks=None, blocked_by=None, relates_to=None, duplicates="TEST-2", clones=None)
        config = plugin._get_link_config(args)  # pylint: disable=protected-access
        assert config["link_type"] == "Duplicate"

        # Test clones
        args = Namespace(blocks=None, blocked_by=None, relates_to=None, duplicates=None, clones="TEST-2")
        config = plugin._get_link_config(args)  # pylint: disable=protected-access
        assert config["link_type"] == "Cloners"

    def test_get_link_config_no_type(self):
        """Test _get_link_config when no link type is specified."""
        plugin = AddLinkPlugin()

        args = Namespace(blocks=None, blocked_by=None, relates_to=None, duplicates=None, clones=None)

        with pytest.raises(AddLinkError, match="No link type specified"):
            plugin._get_link_config(args)  # pylint: disable=protected-access
