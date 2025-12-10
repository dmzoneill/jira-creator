#!/usr/bin/env python
"""
Update description plugin for jira-creator.

This plugin implements the update-description command, allowing users to
update the description of Jira issues from files or stdin.
"""

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Dict, List

from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.exceptions.exceptions import UpdateDescriptionError


class UpdateDescriptionPlugin(JiraPlugin):
    """Plugin for updating the description of Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "update-description"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Update the description of a Jira issue from file or stdin"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Issue Creation & Management"

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ["update-description AAP-12345 description.md", "cat description.txt | update-description AAP-12345 -"]

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")

        input_group = parser.add_mutually_exclusive_group(required=True)
        input_group.add_argument(
            "--file",
            type=str,
            help="File containing the new description",
        )
        input_group.add_argument(
            "--stdin",
            action="store_true",
            help="Read description from stdin",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the update-description command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        # Read description content
        if args.file:
            description = self._read_from_file(args.file)
        elif args.stdin:
            description = self._read_from_stdin()
        else:
            raise UpdateDescriptionError("No input source specified")

        try:
            self.rest_operation(client, issue_key=args.issue_key, description=description)
            print(f"✅ Updated description for {args.issue_key}")
            return True

        except UpdateDescriptionError as e:
            msg = f"❌ Failed to update description for {args.issue_key}: {e}"
            print(msg)
            raise UpdateDescriptionError(e) from e

    def _read_from_file(self, file_path: str) -> str:
        """
        Read description content from file.

        Arguments:
            file_path: Path to the file

        Returns:
            str: File contents

        Raises:
            UpdateDescriptionError: If file cannot be read
        """
        path = Path(file_path)
        if not path.exists():
            raise UpdateDescriptionError(f"File not found: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except (OSError, IOError) as e:
            raise UpdateDescriptionError(f"Failed to read file: {e}") from e

    def _read_from_stdin(self) -> str:
        """
        Read description content from stdin.

        Returns:
            str: Content from stdin
        """
        return sys.stdin.read()

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to update description.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key' and 'description'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        description = kwargs["description"]

        path = f"/rest/api/2/issue/{issue_key}"
        payload = {"fields": {"description": description}}

        return client.request("PUT", path, json_data=payload)
