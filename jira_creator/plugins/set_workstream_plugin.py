#!/usr/bin/env python
"""
Set workstream plugin for jira-creator.

This plugin implements the set-workstream command, allowing users to
change the workstream of Jira issues.
"""

from argparse import ArgumentParser
from typing import Any, Dict

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.plugins.setter_base import SetterPlugin


class SetWorkstreamPlugin(SetterPlugin):
    """Plugin for setting the workstream of Jira issues."""

    @property
    def field_name(self) -> str:
        """Return the field name."""
        return "workstream"

    @property
    def argument_name(self) -> str:
        """Return the argument name."""
        return "workstream_id"

    @property
    def argument_help(self) -> str:
        """Return help text for the workstream argument."""
        return "The workstream ID (optional, uses default if not provided)"

    def register_additional_arguments(self, parser: ArgumentParser) -> None:
        """Override to make workstream_id optional."""
        # Remove the default positional argument
        # pylint: disable=protected-access
        parser._positionals._actions = [
            action for action in parser._positionals._actions if action.dest != self.argument_name
        ]
        # pylint: enable=protected-access

        # Add as optional argument
        parser.add_argument(
            "--workstream-id",
            dest="workstream_id",
            help=self.argument_help,
            default=None,
        )

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to set workstream.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key' and 'value'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        workstream_id = kwargs["value"]

        # Get workstream field from environment
        workstream_field = EnvFetcher.get("JIRA_WORKSTREAM_FIELD")

        # Use default if not provided
        if not workstream_id:
            workstream_id = EnvFetcher.get("JIRA_WORKSTREAM_ID")

        path = f"/rest/api/2/issue/{issue_key}"
        payload = {"fields": {workstream_field: [{"id": workstream_id}]}}

        return client.request("PUT", path, json_data=payload)

    def format_success_message(self, issue_key: str, value: Any) -> str:
        """Format success message for workstream."""
        if value:
            return f"✅ Workstream set to ID '{value}'"
        return "✅ Workstream set to default value"
