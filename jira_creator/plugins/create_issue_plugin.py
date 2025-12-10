#!/usr/bin/env python
"""
Create issue plugin for jira-creator.

This plugin implements the create-issue command, allowing users to create
Jira issues using templates and AI-powered description enhancement.
"""

import json
import os
import subprocess
import tempfile
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Dict, List

import yaml

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.logger import get_logger
from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.exceptions.exceptions import AiError, CreateIssueError
from jira_creator.providers import get_ai_provider
from jira_creator.rest.prompts import IssueType, PromptLibrary
from jira_creator.templates.template_loader import TemplateLoader

logger = get_logger("create_issue")


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

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Issue Creation & Management"

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return [
            "create-issue bug 'Login page crashes on submit'",
            "create-issue story 'Add password reset feature' --story-points 5",
            "create-issue task 'Update documentation' --edit",
        ]

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
        parser.add_argument(
            "--input-file",
            type=str,
            help="JSON or YAML file with field values (enables non-interactive mode)",
        )
        parser.add_argument(
            "--story-points",
            type=int,
            help="Story points to assign (for stories)",
        )
        parser.add_argument(
            "--output",
            choices=["text", "json"],
            default="text",
            help="Output format (default: text)",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Only output the issue key (implies --output text)",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the create-issue command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        logger.info("Creating %s issue: %s", args.type, args.summary)
        logger.debug("Execute args: edit=%s, dry_run=%s, no_ai=%s", args.edit, args.dry_run, args.no_ai)

        try:
            # Load template
            logger.debug("Loading template for issue type: %s", args.type)
            template_loader = TemplateLoader(issue_type=args.type.lower())
            fields = template_loader.get_fields()

            # Gather field values (from file or interactive)
            if args.input_file:
                field_values = self._load_field_values_from_file(args.input_file, fields)
            else:
                field_values = self._gather_field_values(fields, args.edit)

            # Render description
            description = template_loader.render_description(field_values)

            # Optional editing (skip if input-file provided)
            if args.edit and not args.input_file:
                description = self._edit_description(description)

            # AI enhancement (unless disabled)
            if not args.no_ai:
                try:
                    description = self._enhance_with_ai(description, args.type)
                except AiError as e:
                    print(f"❌ AI enhancement failed: {e}")
                    print("⚠️  Issue creation aborted. Use --no-ai to skip AI enhancement.")
                    return False

            # Build payload
            payload = self._build_payload(args.summary, description, args.type, field_values)

            # Add story points if provided
            if args.story_points is not None and args.type.lower() == "story":
                story_points_field = EnvFetcher.get("JIRA_STORY_POINTS_FIELD", default="customfield_12310243")
                payload["fields"][story_points_field] = args.story_points

            # Dry run or create
            if args.dry_run:
                self._show_dry_run(args.summary, description, payload)
                return True

            # Create the issue
            result = self.rest_operation(client, payload=payload)
            issue_key = result.get("key")
            issue_id = result.get("id")
            jira_url = EnvFetcher.get("JIRA_URL")

            # Output based on format
            self._output_result(args, issue_key, issue_id, jira_url, args.story_points)
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

    def _load_field_values_from_file(self, file_path: str, expected_fields: List[str]) -> Dict[str, str]:
        """
        Load field values from JSON or YAML file.

        Arguments:
            file_path: Path to the input file
            expected_fields: List of expected field names from template

        Returns:
            Dict[str, str]: Field values

        Raises:
            CreateIssueError: If file cannot be read or parsed
        """
        path = Path(file_path)
        if not path.exists():
            raise CreateIssueError(f"Input file not found: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Try to parse as JSON first, then YAML
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                try:
                    data = yaml.safe_load(content)
                except yaml.YAMLError as e:
                    raise CreateIssueError(f"Failed to parse input file as JSON or YAML: {e}") from e

            # Validate that all expected fields are present
            missing_fields = [field for field in expected_fields if field not in data]
            if missing_fields:
                raise CreateIssueError(f"Missing required fields in input file: {', '.join(missing_fields)}")

            return data

        except (OSError, IOError) as e:
            raise CreateIssueError(f"Failed to read input file: {e}") from e

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
        editor_func = self.get_dependency("editor_func", lambda: subprocess.call)

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as tmp:
            tmp.write(description)
            tmp.flush()
            tmp_name = tmp.name

        try:
            editor = os.environ.get("EDITOR", "vim")
            editor_func([editor, tmp_name])

            # Reopen the file to read the edited content
            with open(tmp_name, "r", encoding="utf-8") as f:
                return f.read()
        finally:
            # Clean up the temporary file
            os.unlink(tmp_name)

    # jscpd:ignore-end

    def _enhance_with_ai(self, description: str, issue_type: str) -> str:
        """Enhance description using AI provider."""
        ai_provider = self.get_dependency("ai_provider", lambda: get_ai_provider(EnvFetcher.get("JIRA_AI_PROVIDER")))

        # Get appropriate prompt for issue type
        issue_type_enum = IssueType[issue_type.upper()]
        prompt = PromptLibrary.get_prompt(issue_type_enum)

        return ai_provider.improve_text(prompt, description)

    def _build_payload(
        self, summary: str, description: str, issue_type: str, field_values: Dict[str, str] = None
    ) -> Dict[str, Any]:
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

        # Handle affected version for bugs
        if issue_type.lower() == "bug":
            # Priority: template field > environment variable > default
            template_version = field_values.get("Affected Version", "").strip() if field_values else ""
            final_version = template_version or affects_version or "2.5"
            payload["fields"]["versions"] = [{"name": final_version}]
        elif affects_version:
            # For non-bugs, only add if environment variable is set
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
        """Display dry run information with validation checks."""
        print("\n" + "=" * 50)
        print("DRY RUN - Issue Preview")
        print("=" * 50)

        # Run validation checks
        self._validate_issue_data(summary, description, payload)

        # Show preview
        print(f"\n📋 Summary: {summary}")
        print("\n📄 Description:")
        print("-" * 50)
        print(description[:500] + ("..." if len(description) > 500 else ""))
        print("-" * 50)
        print("\n🔧 JSON Payload:")
        print("-" * 50)
        print(json.dumps(payload, indent=2))
        print("=" * 50)

    def _validate_issue_data(self, summary: str, description: str, payload: Dict[str, Any]) -> bool:
        """Validate issue data and print results."""
        validation_passed = True
        print("\n🔍 Validation Checks:")
        print("-" * 50)

        # Check summary length
        validation_passed &= self._validate_length(
            "Summary", len(summary), 255, f"✓ Summary length: {len(summary)}/255 characters"
        )

        # Check description length
        validation_passed &= self._validate_length(
            "Description", len(description), 32000, f"✓ Description length: {len(description)}/32000 characters"
        )

        # Check required fields
        fields = payload.get("fields", {})
        validation_passed &= self._validate_required_field(fields, "project", "key", "Missing project key")
        validation_passed &= self._validate_required_field(fields, "issuetype", "name", "Missing issue type")

        # Check epic link for stories
        self._check_epic_link(fields)

        print("-" * 50)
        status_msg = "✅ All validation checks passed" if validation_passed else "❌ Validation failed"
        print(status_msg)

        return validation_passed

    def _validate_length(self, field_name: str, current: int, max_len: int, success_msg: str) -> bool:
        """Validate field length."""
        if current > max_len:
            print(f"❌ {field_name} exceeds {max_len} character limit")
            return False
        print(success_msg)
        return True

    def _validate_required_field(self, fields: Dict[str, Any], field: str, key: str, error_msg: str) -> bool:
        """Validate required field exists."""
        value = fields.get(field, {}).get(key)
        if not value:
            print(f"❌ {error_msg}")
            return False
        print(f"✓ {field.capitalize()}: {value}")
        return True

    def _check_epic_link(self, fields: Dict[str, Any]) -> None:
        """Check epic link for stories (warning only)."""
        if fields.get("issuetype", {}).get("name") == "Story":
            epic_field = EnvFetcher.get("JIRA_EPIC_FIELD", default="")
            if epic_field and epic_field in fields:
                print(f"✓ Epic link: {fields[epic_field]}")
            else:
                print("⚠️  No epic link specified for story")

    def _output_result(
        self, args: Namespace, issue_key: str, issue_id: str, jira_url: str, story_points: int = None
    ) -> None:
        """
        Output the result based on format preference.

        Arguments:
            args: Command arguments
            issue_key: Created issue key
            issue_id: Created issue ID
            jira_url: Base JIRA URL
            story_points: Story points if set
        """
        if args.quiet:
            # Just output the issue key
            print(issue_key)
        elif args.output == "json":
            # JSON output
            result = {
                "key": issue_key,
                "id": issue_id,
                "url": f"{jira_url}/browse/{issue_key}",
            }
            if story_points is not None:
                result["story_points"] = story_points
            print(json.dumps(result, indent=2))
        else:
            # Default text output
            print(f"✅ Issue created: {issue_key}")
            print(f"🔗 {jira_url}/browse/{issue_key}")
            if story_points is not None:
                print(f"📊 Story points: {story_points}")
