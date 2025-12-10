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
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.logger import get_logger
from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.exceptions.exceptions import EditDescriptionError, EditIssueError, FetchDescriptionError
from jira_creator.providers import get_ai_provider
from jira_creator.rest.prompts import IssueType, PromptLibrary

logger = get_logger("edit_issue")


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

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Issue Creation & Management"

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ["edit-issue AAP-12345"]

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument("--no-ai", action="store_true", help="Skip AI text improvement")
        parser.add_argument(
            "--lint",
            action="store_true",
            help="Run interactive linting on the description",
        )
        parser.add_argument(
            "--acceptance-criteria",
            action="store_true",
            help="Edit acceptance criteria instead of description",
        )
        parser.add_argument(
            "--ai-from-description",
            action="store_true",
            help="Generate acceptance criteria from issue description using AI (requires --acceptance-criteria)",
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
        logger.info("Editing issue %s", args.issue_key)

        try:
            # Check for conflicting flags
            if args.ai_from_description and not args.acceptance_criteria:
                print("⚠️  --ai-from-description requires --acceptance-criteria flag")
                return False

            # Handle acceptance criteria editing
            if args.acceptance_criteria:
                return self._edit_acceptance_criteria(client, args)

            # Handle description editing (original behavior)
            return self._edit_description_flow(client, args)

        except EditIssueError as e:
            msg = f"❌ Failed to edit issue: {e}"
            logger.error("Edit issue failed: %s", e)
            print(msg)
            raise EditIssueError(e) from e

    def _edit_description_flow(self, client: Any, args: Namespace) -> bool:
        """Handle the description editing workflow."""
        # Fetch current description
        print(f"📥 Fetching description for {args.issue_key}...")
        current_description = self._fetch_description(client, args.issue_key)

        # Edit description
        print("📝 Opening editor...")
        edited_description = self._edit_text(current_description)

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
                logger.warning("AI enhancement failed: %s", e)
                print(f"⚠️  AI enhancement failed, using edited text: {e}")

        # Optional linting
        if args.lint:
            edited_description = self._lint_description(edited_description)

        # Update the issue
        self.rest_operation(client, issue_key=args.issue_key, description=edited_description)

        print(f"✅ Successfully updated description for {args.issue_key}")
        logger.info("Successfully updated description for %s", args.issue_key)
        return True

    def _edit_acceptance_criteria(self, client: Any, args: Namespace) -> bool:
        """Handle the acceptance criteria editing workflow."""
        logger.info("Editing acceptance criteria for %s", args.issue_key)

        # Check if using AI generation
        if args.ai_from_description:
            print(f"🤖 Generating acceptance criteria from description for {args.issue_key}...")
            criteria = self._generate_ac_from_description(client, args.issue_key)
        else:
            # Fetch current acceptance criteria
            print(f"📥 Fetching acceptance criteria for {args.issue_key}...")
            current_criteria = self._fetch_acceptance_criteria(client, args.issue_key)

            # Edit criteria
            print("📝 Opening editor...")
            criteria = self._edit_text(current_criteria or "")

            # Check if criteria changed
            if criteria == current_criteria:
                print("ℹ️  No changes made to acceptance criteria")
                return True

        # Update the issue
        self._update_acceptance_criteria(client, args.issue_key, criteria)

        print(f"✅ Successfully updated acceptance criteria for {args.issue_key}")
        logger.info("Successfully updated acceptance criteria for %s", args.issue_key)
        return True

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
    def _edit_text(self, text: str) -> str:
        """Open text in editor for manual editing."""
        editor_func = self.get_dependency("editor_func", subprocess.call)

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as tmp:
            tmp.write(text)
            tmp.flush()

            editor = os.environ.get("EDITOR", "vim")
            editor_func([editor, tmp.name])

            tmp.seek(0)
            edited = tmp.read()

            if not edited.strip():
                raise EditDescriptionError("Edited text cannot be empty")

            return edited

    # jscpd:ignore-end

    def _fetch_acceptance_criteria(self, client: Any, issue_key: str) -> str:
        """Fetch the current acceptance criteria of an issue."""
        try:
            criteria_field = EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD")
            path = f"/rest/api/2/issue/{issue_key}?fields={criteria_field}"
            response = client.request("GET", path)

            criteria = response.get("fields", {}).get(criteria_field, "")
            return criteria or ""

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to fetch acceptance criteria: %s", e)
            return ""

    def _generate_ac_from_description(self, client: Any, issue_key: str) -> str:
        """Generate acceptance criteria from issue description using AI."""
        try:
            # Fetch the issue to get its description and summary
            path = f"/rest/api/2/issue/{issue_key}"
            issue_data = client.request("GET", path)

            description = issue_data.get("fields", {}).get("description", "")
            if not description:
                raise EditIssueError(f"Issue {issue_key} has no description to generate from")

            summary = issue_data.get("fields", {}).get("summary", "")

            # Generate acceptance criteria using AI
            provider_name = EnvFetcher.get("JIRA_AI_PROVIDER", default="openai")
            provider = get_ai_provider(provider_name)

            prompt = f"""Based on the following Jira issue, generate clear and testable acceptance criteria in \
markdown checklist format.

Issue Summary: {summary}

Issue Description:
{description}

Generate acceptance criteria as a markdown checklist (using * [ ] format). Focus on:
- Functional requirements
- User-facing behavior
- Edge cases
- Testing scenarios

Acceptance Criteria:"""

            criteria = provider.complete(prompt)

            if not criteria or not criteria.strip():
                raise EditIssueError("AI generated empty acceptance criteria")

            return criteria.strip()

        except Exception as e:
            raise EditIssueError(f"Failed to generate acceptance criteria: {e}") from e

    def _update_acceptance_criteria(self, client: Any, issue_key: str, criteria: str) -> None:
        """Update the acceptance criteria field of an issue."""
        try:
            criteria_field = EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD")
            path = f"/rest/api/2/issue/{issue_key}"
            payload = {"fields": {criteria_field: criteria}}

            client.request("PUT", path, json_data=payload)

        except Exception as e:
            raise EditIssueError(f"Failed to update acceptance criteria: {e}") from e

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
