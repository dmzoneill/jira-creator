#!/usr/bin/env python
"""
Set story points plugin for jira-creator.

This plugin implements the set-story-points command, allowing users to
change the story points of Jira issues.
"""

from argparse import ArgumentParser
from typing import Any, Dict

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.plugins.setter_base import SetterPlugin


class SetStoryPointsPlugin(SetterPlugin):
    """Plugin for setting the story points of Jira issues."""

    @property
    def field_name(self) -> str:
        """Return the field name."""
        return "story points"

    @property
    def argument_name(self) -> str:
        """Return the argument name."""
        return "points"

    @property
    def argument_help(self) -> str:
        """Return help text for the points argument."""
        return "The story points value (integer)"

    def register_additional_arguments(self, parser: ArgumentParser) -> None:
        """Override to add type validation for points."""
        # pylint: disable=protected-access
        # Remove the default positional argument - necessary to override parent class behavior
        parser._positionals._actions = [
            action for action in parser._positionals._actions if action.dest != self.argument_name
        ]
        # pylint: enable=protected-access

        # Add with type validation
        parser.add_argument("points", type=int, help=self.argument_help)

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to set story points.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key' and 'value'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        points = kwargs["value"]

        # Get story points field from environment
        story_points_field = EnvFetcher.get("JIRA_STORY_POINTS_FIELD")

        path = f"/rest/api/2/issue/{issue_key}"
        payload = {"fields": {story_points_field: points}}

        return client.request("PUT", path, json_data=payload)
