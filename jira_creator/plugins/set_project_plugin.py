#!/usr/bin/env python
"""
Set project plugin for jira-creator.

This plugin implements the set-project command, allowing users to
change the project of Jira issues.
"""

from typing import Any, Dict

from jira_creator.plugins.setter_base import SetterPlugin


class SetProjectPlugin(SetterPlugin):
    """Plugin for setting the project of Jira issues."""

    @property
    def field_name(self) -> str:
        """Return the field name."""
        return "project"

    @property
    def argument_name(self) -> str:
        """Return the argument name."""
        return "project"

    @property
    def argument_help(self) -> str:
        """Return help text for the project argument."""
        return "The project key to move the issue to"

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to set project.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key' and 'value'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        project = kwargs["value"]

        path = f"/rest/api/2/issue/{issue_key}"
        payload = {"fields": {"project": {"key": project}}}

        return client.request("PUT", path, json_data=payload)
