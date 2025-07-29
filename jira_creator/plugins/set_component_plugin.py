#!/usr/bin/env python
"""
Set component plugin for jira-creator.

This plugin implements the set-component command, allowing users to
change the component of Jira issues.
"""

from typing import Any, Dict

from jira_creator.plugins.setter_base import SetterPlugin


class SetComponentPlugin(SetterPlugin):
    """Plugin for setting the component of Jira issues."""

    @property
    def field_name(self) -> str:
        """Return the field name."""
        return "component"

    @property
    def argument_name(self) -> str:
        """Return the argument name."""
        return "component"

    @property
    def argument_help(self) -> str:
        """Return help text for the component argument."""
        return "The component name to set for the issue"

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to set component.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key' and 'value'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        component = kwargs["value"]

        path = f"/rest/api/2/issue/{issue_key}/components"
        payload = {"components": [{"name": component}]}

        return client.request("PUT", path, json_data=payload)
