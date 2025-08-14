#!/usr/bin/env python
"""
Create issue plugin for jira-creator.

This plugin implements the create-issue command, allowing users to create
Jira issues using templates and AI-powered description enhancement.
"""

import os
import subprocess
import tempfile
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import AiError, CreateIssueError
from jira_creator.plugins.base import JiraPlugin
from jira_creator.providers import get_ai_provider
from jira_creator.rest.prompts import IssueType, PromptLibrary
from jira_creator.templates.template_loader import TemplateLoader


class CreateIssuePlugin(JiraPlugin):
    """Plugin for creating Jira issues with templates and AI enhancement."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "create-issue"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Create a new Jira issue using templates"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument(
            "type",
            choices=["bug", "story", "epic", "task"],
            help="Type of issue to create",
        )
        parser.add_argument("summary", help="Issue summary/title")
        parser.add_argument(
            "-e",
            "--edit",
            action="store_true",
            help="Open editor to modify the description before submission",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview the issue without creating it",
        )
        parser.add_argument("--no-ai", action="store_true", help="Skip AI text improvement")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the create-issue command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        try:
            # Load template
            template_loader = TemplateLoader(issue_type=args.type.lower())
            fields = template_loader.get_fields()

            # Gather field values
            field_values = self._gather_field_values(fields, args.edit)

            # Render description
            description = template_loader.render_description(field_values)

            # Optional editing
            if args.edit:
                description = self._edit_description(description)

            # AI enhancement (unless disabled)
            if not args.no_ai:
                try:
                    description = self._enhance_with_ai(description, args.type)
                except AiError as e:
                    print(f"⚠️  AI enhancement failed, using original text: {e}")

            # Build payload
            payload = self._build_payload(args.summary, description, args.type)

            # Dry run or create
            if args.dry_run:
                self._show_dry_run(args.summary, description, payload)
                return True

            # Create the issue
            result = self.rest_operation(client, payload=payload)
            issue_key = result.get("key")

            print(f"✅ Issue created: {issue_key}")
            print(f"🔗 {EnvFetcher.get('JIRA_URL')}/browse/{issue_key}")
            return True

        except CreateIssueError as e:
            msg = f"❌ Failed to create issue: {e}"
            print(msg)
            raise CreateIssueError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to create an issue.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'payload'

        Returns:
            Dict[str, Any]: API response with created issue details
        """
        payload = kwargs["payload"]

        path = "/rest/api/2/issue/"
        return client.request("POST", path, json_data=payload)

    def _gather_field_values(self, fields: List[str], edit_mode: bool) -> Dict[str, str]:
        """Gather values for template fields."""
        field_values = {}

        if edit_mode:
            # Use placeholders in edit mode
            for field in fields:
                field_values[field] = f"{{{{{field}}}}}"
        else:
            # Interactive input
            print("\n📝 Please provide the following information:")
            print("-" * 40)

            for field in fields:
                value = input(f"{field}: ").strip()
                field_values[field] = value

        return field_values

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
            return tmp.read()

    # jscpd:ignore-end

    def _enhance_with_ai(self, description: str, issue_type: str) -> str:
        """Enhance description using AI provider."""
        ai_provider = self.get_dependency("ai_provider", lambda: get_ai_provider(EnvFetcher.get("JIRA_AI_PROVIDER")))

        # Get appropriate prompt for issue type
        issue_type_enum = IssueType[issue_type.upper()]
        prompt = PromptLibrary.get_prompt(issue_type_enum)

        return ai_provider.improve_text(prompt, description)

    def _build_payload(self, summary: str, description: str, issue_type: str) -> Dict[str, Any]:
        """Build the Jira API payload."""
        # Get configuration from environment
        project_key = EnvFetcher.get("JIRA_PROJECT_KEY")
        affects_version = EnvFetcher.get("JIRA_AFFECTS_VERSION") or ""
        component_name = EnvFetcher.get("JIRA_COMPONENT_NAME") or ""
        priority = EnvFetcher.get("JIRA_PRIORITY") or "Normal"
        epic_field = EnvFetcher.get("JIRA_EPIC_FIELD") or ""

        # Build basic payload
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type.capitalize()},
                "priority": {"name": priority},
            }
        }

        # Add optional fields
        if affects_version:
            payload["fields"]["versions"] = [{"name": affects_version}]

        if component_name:
            payload["fields"]["components"] = [{"name": component_name}]

        # Add epic link for stories
        if issue_type.lower() == "story" and epic_field:
            epic_key = EnvFetcher.get("JIRA_EPIC_KEY", default="")
            if epic_key:
                payload["fields"][epic_field] = epic_key

        return payload

    def _show_dry_run(self, summary: str, description: str, payload: Dict[str, Any]) -> None:
        """Display dry run information."""
        print("\n" + "=" * 50)
        print("DRY RUN - Issue Preview")
        print("=" * 50)
        print(f"\n📋 Summary: {summary}")
        print("\n📄 Description:")
        print("-" * 50)
        print(description)
        print("-" * 50)
        print("\n🔧 JSON Payload:")
        print("-" * 50)

        import json

        print(json.dumps(payload, indent=2))
        print("=" * 50)
