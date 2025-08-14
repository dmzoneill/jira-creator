#!/usr/bin/env python
"""
Migrate plugin for jira-creator.

This plugin implements the migrate command, allowing users to migrate
Jira issues to a new issue type.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.exceptions.exceptions import MigrateError
from jira_creator.plugins.base import JiraPlugin


class MigratePlugin(JiraPlugin):
    """Plugin for migrating issues to new types."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "migrate"

    @property
    def help_text(self) -> str:
        """Return the command help text."""
        return "Migrate issue to a new type"

    # jscpd:ignore-start
    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments with the argument parser."""
        parser.add_argument("issue_key", help="The Jira issue id/key")
        parser.add_argument("new_type", help="New issue type")

    def execute(self, client: Any, args: Namespace) -> bool:
        """Execute the migrate command."""
        # jscpd:ignore-end
        try:
            result = self.rest_operation(client, issue_key=args.issue_key, new_type=args.new_type)
            new_key = result.get("new_key", args.issue_key)
            print(f"✅ Migrated {args.issue_key} to {new_key}: {client.jira_url}/browse/{new_key}")
            return True
        except MigrateError as e:
            msg = f"❌ Migration failed: {e}"
            print(msg)
            raise MigrateError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to migrate an issue.

        Arguments:
            client: JiraClient instance
            **kwargs: Must contain 'issue_key' and 'new_type'

        Returns:
            Dict[str, Any]: API response with new_key
        """
        issue_key = kwargs["issue_key"]
        new_type = kwargs["new_type"]

        try:
            # Get old issue details
            fields = client.request("GET", f"/rest/api/2/issue/{issue_key}")["fields"]
            summary = fields.get("summary", f"Migrated from {issue_key}")
            description = fields.get("description", f"Migrated from {issue_key}")

            # Create new issue payload directly
            fields = {
                "project": {"key": client.project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": new_type.capitalize()},
                "priority": {"name": client.priority},
                "components": [{"name": client.component_name}],
            }

            if client.affects_version != "":
                fields["versions"] = [{"name": client.affects_version}]

            if new_type.lower() == "epic":
                fields[client.epic_field] = summary

            payload = {"fields": fields}
            new_key = client.request("POST", "/rest/api/2/issue/", json_data=payload)["key"]

            # Add migration comment to old issue
            client.request(
                "POST",
                f"/rest/api/2/issue/{issue_key}/comment",
                json_data={
                    "body": f"Migrated to [{new_key}]({client.jira_url}/browse/{new_key}) as a {new_type.upper()}."
                },
            )

            # Try to transition old issue to done/closed
            transitions = client.request("GET", f"/rest/api/2/issue/{issue_key}/transitions")["transitions"]
            transition_id = next(
                (t["id"] for t in transitions if t["name"].lower() in ["done", "closed", "cancelled"]),
                None,
            )
            if not transition_id and transitions:
                transition_id = transitions[0]["id"]

            if transition_id:
                client.request(
                    "POST",
                    f"/rest/api/2/issue/{issue_key}/transitions",
                    json_data={"transition": {"id": transition_id}},
                )

            return {"new_key": new_key}

        except Exception as e:
            raise MigrateError(f"Migration failed: {e}") from e
