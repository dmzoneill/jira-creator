#!/usr/bin/env python
"""Tests for the set component plugin."""

from argparse import Namespace
from unittest.mock import Mock

import pytest

from jira_creator.exceptions.exceptions import SetComponentError
from jira_creator.plugins.set_component_plugin import SetComponentPlugin


class TestSetComponentPlugin:
    """Test cases for SetComponentPlugin."""

    def test_plugin_properties(self):
        """Test plugin properties are set correctly."""
        plugin = SetComponentPlugin()
        assert plugin.command_name == "set-component"
        assert plugin.help_text == "Set the component of a Jira issue"
        assert plugin.field_name == "component"
        assert plugin.argument_name == "component"
        assert plugin.argument_help == "The component name to set for the issue"

    def test_register_arguments(self):
        """Test argument registration."""
        plugin = SetComponentPlugin()
        mock_parser = Mock()

        plugin.register_arguments(mock_parser)

        # Verify add_argument was called with correct parameters
        assert mock_parser.add_argument.call_count == 2
        calls = mock_parser.add_argument.call_args_list

        # First argument: issue_key
        assert calls[0][0] == ("issue_key",)
        assert calls[0][1]["help"] == "The Jira issue key (e.g., PROJ-123)"

        # Second argument: component
        assert calls[1][0] == ("component",)
        assert calls[1][1]["help"] == "The component name to set for the issue"

    def test_rest_operation(self):
        """Test the REST operation directly."""
        plugin = SetComponentPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        result = plugin.rest_operation(mock_client, issue_key="TEST-123", value="Backend")

        # Verify the request
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123/components",
            json_data={"components": [{"name": "Backend"}]},
        )
        assert result == {"key": "TEST-123"}

    def test_execute_success(self, capsys):
        """Test successful execution."""
        plugin = SetComponentPlugin()
        mock_client = Mock()
        mock_client.request.return_value = {"key": "TEST-123"}

        args = Namespace(issue_key="TEST-123", component="Frontend")

        result = plugin.execute(mock_client, args)

        # Verify success
        assert result is True
        mock_client.request.assert_called_once_with(
            "PUT",
            "/rest/api/2/issue/TEST-123/components",
            json_data={"components": [{"name": "Frontend"}]},
        )

        # Verify print output
        captured = capsys.readouterr()
        assert "✅ Component for TEST-123 set to 'Frontend'" in captured.out

    def test_execute_failure(self, capsys):
        """Test execution with API failure."""
        plugin = SetComponentPlugin()
        mock_client = Mock()
        mock_client.request.side_effect = SetComponentError("Component not found")

        args = Namespace(issue_key="TEST-123", component="InvalidComponent")

        # Verify exception is raised
        with pytest.raises(SetComponentError) as exc_info:
            plugin.execute(mock_client, args)

        # Verify the exception message
        assert str(exc_info.value) == "Component not found"

        # Verify print output
        captured = capsys.readouterr()
        assert "❌ Failed to set component: Component not found" in captured.out

    def test_execute_with_different_components(self):
        """Test execute with different component names."""
        plugin = SetComponentPlugin()
        mock_client = Mock()

        test_components = ["Backend", "Frontend", "Database", "UI/UX", "Security"]

        for component in test_components:
            mock_client.reset_mock()
            args = Namespace(issue_key="TEST-123", component=component)

            result = plugin.execute(mock_client, args)

            assert result is True
            # Verify the component was passed correctly
            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["components"][0]["name"] == component

    def test_rest_operation_with_special_characters(self):
        """Test REST operation with component names containing special characters."""
        plugin = SetComponentPlugin()
        mock_client = Mock()

        special_components = [
            "Backend-API",
            "UI/UX Design",
            "Security & Compliance",
            "Data (Analytics)",
            "Mobile [iOS]",
        ]

        for component in special_components:
            mock_client.reset_mock()

            plugin.rest_operation(mock_client, issue_key="TEST-456", value=component)

            # Verify special characters are preserved
            call_args = mock_client.request.call_args[1]["json_data"]
            assert call_args["components"][0]["name"] == component
