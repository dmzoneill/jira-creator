#!/usr/bin/env python
"""
Edit issue plugin for jira-creator.

This plugin implements the edit-issue command, allowing users to edit
Jira issue descriptions with AI enhancement and linting capabilities.
"""

import os
import subprocess
import tempfile
from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import (
    EditDescriptionError,
    EditIssueError,
    FetchDescriptionError,
)
from jira_creator.plugins.base import JiraPlugin
from jira_creator.providers import get_ai_provider
from jira_creator.rest.prompts import IssueType, PromptLibrary


class EditIssuePlugin(JiraPlugin):
    """Plugin for editing Jira issue descriptions."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "edit-issue"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Edit a Jira issue description"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument("--no-ai", action="store_true", help="Skip AI text improvement")
        parser.add_argument(
            "--lint",
            action="store_true",
            help="Run interactive linting on the description",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the edit-issue command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            # Fetch current description
            print(f"📥 Fetching description for {args.issue_key}...")
            current_description = self._fetch_description(client, args.issue_key)

            # Edit description
            print("📝 Opening editor...")
            edited_description = self._edit_description(current_description)

            # Check if description changed
            if edited_description == current_description:
                print("ℹ️  No changes made to description")
                return True

            # AI enhancement (unless disabled)
            if not args.no_ai:
                print("🤖 Enhancing description with AI...")
                issue_type = self._get_issue_type(client, args.issue_key)
                try:
                    edited_description = self._enhance_with_ai(edited_description, issue_type)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"⚠️  AI enhancement failed, using edited text: {e}")

            # Optional linting
            if args.lint:
                edited_description = self._lint_description(edited_description)

            # Update the issue
            self.rest_operation(client, issue_key=args.issue_key, description=edited_description)

            print(f"✅ Successfully updated description for {args.issue_key}")
            return True

        except EditIssueError as e:
            msg = f"❌ Failed to edit issue: {e}"
            print(msg)
            raise EditIssueError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to update issue description.

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

    def _fetch_description(self, client: Any, issue_key: str) -> str:
        """Fetch the current description of an issue."""
        try:
            path = f"/rest/api/2/issue/{issue_key}?fields=description"
            response = client.request("GET", path)

            description = response.get("fields", {}).get("description", "")
            if not description:
                raise FetchDescriptionError("Issue has no description")

            return description

        except Exception as e:
            raise FetchDescriptionError(f"Failed to fetch description: {e}") from e

    def _get_issue_type(self, client: Any, issue_key: str) -> str:
        """Get the issue type for determining AI prompt."""
        try:
            path = f"/rest/api/2/issue/{issue_key}?fields=issuetype"
            response = client.request("GET", path)

            issue_type = response.get("fields", {}).get("issuetype", {}).get("name", "")
            return issue_type.upper()

        except Exception:  # pylint: disable=broad-exception-caught
            return "STORY"  # Default to story type

    # jscpd:ignore-start
    def _edit_description(self, description: str) -> str:
        """Open description in editor for manual editing."""
        editor_func = self.get_dependency("editor_func", subprocess.call)

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as tmp:
            tmp.write(description)
            tmp.flush()

            editor = os.environ.get("EDITOR", "vim")
            editor_func([editor, tmp.name])

            tmp.seek(0)
            edited = tmp.read()

            if not edited.strip():
                raise EditDescriptionError("Description cannot be empty")

            return edited

    # jscpd:ignore-end

    def _enhance_with_ai(self, description: str, issue_type: str) -> str:
        """Enhance description using AI provider."""
        ai_provider = self.get_dependency("ai_provider", lambda: get_ai_provider(EnvFetcher.get("JIRA_AI_PROVIDER")))

        # Map issue type to enum
        try:
            issue_type_enum = IssueType[issue_type]
        except KeyError:
            issue_type_enum = IssueType.STORY  # Default

        prompt = PromptLibrary.get_prompt(issue_type_enum)
        return ai_provider.improve_text(prompt, description)

    def _lint_description(self, description: str) -> str:
        """
        Interactively lint the description.

        This is a simplified version - the full implementation would
        integrate with the validate_issue functionality.
        """
        print("\n🔍 Linting description...")
        print("ℹ️  Interactive linting not fully implemented in plugin version")

        # In a full implementation, this would:
        # 1. Run validation checks
        # 2. Show issues to user
        # 3. Allow them to fix issues interactively
        # 4. Repeat until no issues found

        return description
