#!/usr/bin/env python
"""
Set summary plugin for jira-creator.

This plugin implements the set-summary command, allowing users to
change the summary of Jira issues.
"""

from typing import Any, Dict

from jira_creator.plugins.setter_base import SetterPlugin


class SetSummaryPlugin(SetterPlugin):
    """Plugin for setting the summary of Jira issues."""

    @property
    def field_name(self) -> str:
        """Return the field name."""
        return "summary"

    @property
    def argument_name(self) -> str:
        """Return the argument name."""
        return "summary"

    @property
    def argument_help(self) -> str:
        """Return help text for the summary argument."""
        return "The new summary text for the issue"

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to set summary.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key' and 'value'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        summary = kwargs["value"]

        path = f"/rest/api/2/issue/{issue_key}"
        payload = {"fields": {"summary": summary}}

        return client.request("PUT", path, json_data=payload)
