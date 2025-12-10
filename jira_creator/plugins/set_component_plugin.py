#!/usr/bin/env python
"""
Set component plugin for jira-creator.

This plugin implements the set-component command, allowing users to
change the component of Jira issues.
"""

from argparse import Namespace
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.plugin_setter_base import SetterPlugin


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

    def get_fix_capabilities(self) -> List[Dict[str, Any]]:
        """Register fix capabilities for automated issue fixing."""
        return [
            {
                "method_name": "set_default_component",
                "description": "Set component to default value",
                "params": {"issue_key": "str - The JIRA issue key"},
                "conditions": {
                    "problem_patterns": ["component", "Component not set"],
                },
            }
        ]

    def execute_fix(self, client: Any, method_name: str, args: Dict[str, Any]) -> bool:
        """
        Execute a fix method for automated issue fixing.

        Arguments:
            client: JiraClient instance
            method_name: The fix method to execute
            args: Arguments for the fix

        Returns:
            bool: True if fix succeeded, False otherwise
        """
        if method_name == "set_default_component":
            issue_key = args["issue_key"]

            try:
                # Get default component from environment
                default_component = EnvFetcher.get("JIRA_DEFAULT_COMPONENT", default=None)

                if not default_component:
                    # No default configured, can't auto-fix
                    return False

                # Create namespace for execute method
                ns = Namespace(issue_key=issue_key, component=default_component)
                return self.execute(client, ns)
            except Exception:  # pylint: disable=broad-exception-caught
                return False

        return False
