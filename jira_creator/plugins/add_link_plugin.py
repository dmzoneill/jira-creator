#!/usr/bin/env python
"""
Add link plugin for jira-creator.

This plugin implements the add-link command, allowing users to create
issue links between Jira issues (blocks, blocked-by, relates-to, etc.).
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.core.plugin_base import JiraPlugin


class AddLinkError(Exception):
    """Exception raised when adding a link fails."""


class AddLinkPlugin(JiraPlugin):
    """Plugin for creating issue links between Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "add-link"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Create an issue link between two Jira issues"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Issue Relationships"

    def get_plugin_exceptions(self) -> Dict[str, type[Exception]]:
        """Register this plugin's custom exceptions."""
        return {
            "AddLinkError": AddLinkError,
        }

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ["add-link AAP-12345 AAP-12346 blocks", "add-link AAP-12345 AAP-12347 relates-to"]

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The source issue key (e.g., PROJ-123)")

        link_type_group = parser.add_mutually_exclusive_group(required=True)
        link_type_group.add_argument(
            "--blocks",
            metavar="TARGET_KEY",
            help="Target issue that this issue blocks",
        )
        link_type_group.add_argument(
            "--blocked-by",
            metavar="TARGET_KEY",
            help="Target issue that blocks this issue",
        )
        link_type_group.add_argument(
            "--relates-to",
            metavar="TARGET_KEY",
            help="Target issue that relates to this issue",
        )
        link_type_group.add_argument(
            "--duplicates",
            metavar="TARGET_KEY",
            help="Target issue that this issue duplicates",
        )
        link_type_group.add_argument(
            "--clones",
            metavar="TARGET_KEY",
            help="Target issue that this issue clones",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the add-link command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        # Map link type arguments to link configuration
        link_config = self._get_link_config(args)

        try:
            self.rest_operation(
                client,
                source_key=args.issue_key,
                target_key=link_config["target_key"],
                link_type=link_config["link_type"],
                direction=link_config["direction"],
            )

            print(link_config["success_msg"].format(source=args.issue_key, target=link_config["target_key"]))
            return True

        except AddLinkError as e:
            msg = f"❌ Failed to create link: {e}"
            print(msg)
            raise AddLinkError(e) from e

    def _get_link_config(self, args: Namespace) -> Dict[str, str]:
        """
        Get link configuration based on arguments.

        Arguments:
            args: Parsed command arguments

        Returns:
            Dict with link_type, target_key, direction, and success_msg
        """
        if args.blocks:
            return {
                "link_type": "Blocks",
                "target_key": args.blocks,
                "direction": "outward",
                "success_msg": "✅ {source} now blocks {target}",
            }
        if args.blocked_by:
            return {
                "link_type": "Blocks",
                "target_key": args.blocked_by,
                "direction": "inward",
                "success_msg": "✅ {source} is now blocked by {target}",
            }
        if args.relates_to:
            return {
                "link_type": "Relates",
                "target_key": args.relates_to,
                "direction": "outward",
                "success_msg": "✅ {source} now relates to {target}",
            }
        if args.duplicates:
            return {
                "link_type": "Duplicate",
                "target_key": args.duplicates,
                "direction": "outward",
                "success_msg": "✅ {source} now duplicates {target}",
            }
        if args.clones:
            return {
                "link_type": "Cloners",
                "target_key": args.clones,
                "direction": "outward",
                "success_msg": "✅ {source} now clones {target}",
            }
        raise AddLinkError("No link type specified")

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to create an issue link.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'source_key', 'target_key', 'link_type', 'direction'

        Returns:
            Dict[str, Any]: API response
        """
        source_key = kwargs["source_key"]
        target_key = kwargs["target_key"]
        link_type = kwargs["link_type"]
        direction = kwargs["direction"]

        path = "/rest/api/2/issueLink"

        # Build payload based on direction
        if direction == "outward":
            payload = {
                "type": {"name": link_type},
                "inwardIssue": {"key": target_key},
                "outwardIssue": {"key": source_key},
            }
        else:  # inward
            payload = {
                "type": {"name": link_type},
                "inwardIssue": {"key": source_key},
                "outwardIssue": {"key": target_key},
            }

        return client.request("POST", path, json_data=payload)
