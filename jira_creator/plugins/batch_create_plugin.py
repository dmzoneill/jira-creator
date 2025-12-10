#!/usr/bin/env python
"""
Batch create plugin for jira-creator.

This plugin implements the batch-create command, allowing users to create
multiple Jira issues from a directory of JSON/YAML files.
"""

import json
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Dict, List

import yaml

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.logger import get_logger
from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.exceptions.exceptions import BatchCreateError, CreateIssueError
from jira_creator.templates.template_loader import TemplateLoader

logger = get_logger("batch_create")


class BatchCreatePlugin(JiraPlugin):
    """Plugin for batch creating Jira issues from files."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "batch-create"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Create multiple Jira issues from a directory of input files"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Issue Creation & Management"

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ["batch-create /path/to/issues/", "batch-create ./issue-templates/ --dry-run"]

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_type", choices=["story", "bug", "epic", "task", "spike"], help="Issue type")
        parser.add_argument("--input-dir", required=True, help="Directory containing JSON/YAML files")
        parser.add_argument("--pattern", default="*.json", help="File pattern to match (default: *.json)")
        parser.add_argument("--epic", help="Epic to link all stories to")
        parser.add_argument("--no-ai", action="store_true", help="Skip AI enhancement")
        parser.add_argument("--dry-run", action="store_true", help="Validate without creating issues")
        parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")
        parser.add_argument("--continue-on-error", action="store_true", help="Continue if one issue fails")

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the batch-create command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        logger.info("Batch creating %s issues from %s", args.issue_type, args.input_dir)
        logger.debug(
            "Pattern: %s, dry_run: %s, continue_on_error: %s", args.pattern, args.dry_run, args.continue_on_error
        )

        try:
            input_dir = Path(args.input_dir)
            if not input_dir.exists() or not input_dir.is_dir():
                logger.error("Input directory not found: %s", args.input_dir)
                raise BatchCreateError(f"Input directory not found or not a directory: {args.input_dir}")

            # Find all matching files
            files = list(input_dir.glob(args.pattern))
            if not files:
                logger.error("No files matching pattern '%s' found", args.pattern)
                raise BatchCreateError(f"No files matching pattern '{args.pattern}' found in {args.input_dir}")

            logger.info("Found %d file(s) to process", len(files))
            if not args.dry_run:
                print(f"📦 Found {len(files)} file(s) to process")

            # Process each file
            results = []
            errors = []

            for file_path in sorted(files):
                logger.debug("Processing file: %s", file_path)
                try:
                    result = self._process_file(client, file_path, args)
                    results.append(result)
                    logger.debug("Successfully processed: %s", file_path)
                except (CreateIssueError, BatchCreateError) as e:
                    logger.warning("Error processing %s: %s", file_path, e)
                    error_info = {"file": str(file_path), "error": str(e)}
                    errors.append(error_info)

                    if not args.continue_on_error:
                        raise BatchCreateError(f"Failed to process {file_path}: {e}") from e

                    print(f"❌ Failed to process {file_path.name}: {e}")

            # Output results
            if args.dry_run:
                print(f"\n✅ Dry run complete: {len(results)} file(s) validated")
                if errors:
                    print(f"❌ Validation errors: {len(errors)} file(s) failed")
                    for error in errors:
                        print(f"   - {Path(error['file']).name}: {error['error']}")
            else:
                self._output_results(args, results, errors)

            return len(errors) == 0

        except BatchCreateError as e:
            print(f"❌ Batch create failed: {e}")
            raise

    def _process_file(self, client: Any, file_path: Path, args: Namespace) -> Dict[str, Any]:
        """
        Process a single file and create an issue.

        Arguments:
            client: JiraClient instance
            file_path: Path to the input file
            args: Parsed command arguments

        Returns:
            Dict with created issue information
        """
        # Load file content
        data = self._load_file(file_path)

        # Extract title from data or filename
        title = data.pop("title", None) or data.pop("summary", None)
        if not title:
            # Use filename without extension as title
            title = file_path.stem.replace("_", " ").replace("-", " ").title()

        # Get template fields
        template_loader = TemplateLoader(issue_type=args.issue_type.lower())
        expected_fields = template_loader.get_fields()

        # Validate required fields
        missing_fields = [field for field in expected_fields if field not in data]
        if missing_fields:
            raise BatchCreateError(f"Missing required fields in {file_path.name}: {', '.join(missing_fields)}")

        # Render description
        description = template_loader.render_description(data)

        # Build payload
        payload = self._build_payload(title, description, args.issue_type, data)

        # Add epic link if provided
        if args.epic and args.issue_type.lower() == "story":
            epic_field = EnvFetcher.get("JIRA_EPIC_FIELD", default="customfield_12311140")
            payload["fields"][epic_field] = args.epic

        if args.dry_run:
            print(f"✓ Validated: {file_path.name} -> {title}")
            return {"file": str(file_path), "title": title, "dry_run": True}

        # Create the issue
        result = self.rest_operation(client, payload=payload)
        issue_key = result.get("key")
        issue_id = result.get("id")

        print(f"✅ Created {issue_key}: {title}")

        return {
            "file": str(file_path),
            "key": issue_key,
            "id": issue_id,
            "title": title,
        }

    def _load_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Load and parse a JSON or YAML file.

        Arguments:
            file_path: Path to the file

        Returns:
            Dict with file contents

        Raises:
            BatchCreateError: If file cannot be read or parsed
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Try JSON first, then YAML
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                try:
                    return yaml.safe_load(content)
                except yaml.YAMLError as e:
                    raise BatchCreateError(f"Failed to parse {file_path.name}: {e}") from e

        except (OSError, IOError) as e:
            raise BatchCreateError(f"Failed to read {file_path.name}: {e}") from e

    def _build_payload(
        self, summary: str, description: str, issue_type: str, field_values: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Build the JIRA API payload for creating an issue.

        Arguments:
            summary: Issue summary/title
            description: Issue description
            issue_type: Type of issue (story, bug, etc.)
            field_values: Additional field values from template

        Returns:
            Dict: JIRA API payload
        """
        project_key = EnvFetcher.get("JIRA_PROJECT_KEY", default="AAP")

        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type.capitalize()},
            }
        }

        # Add component if specified in environment
        component = EnvFetcher.get("JIRA_COMPONENT")
        if component:
            payload["fields"]["components"] = [{"name": component}]

        # Add priority if specified
        priority = EnvFetcher.get("JIRA_PRIORITY", default="Normal")
        payload["fields"]["priority"] = {"name": priority}

        # Add affects version for bugs
        if issue_type.lower() == "bug":
            version = field_values.get("Affects Version") or EnvFetcher.get("JIRA_AFFECTS_VERSION")
            if version:
                payload["fields"]["versions"] = [{"name": version}]

        return payload

    def _output_results(self, args: Namespace, results: List[Dict], errors: List[Dict]) -> None:
        """
        Output the batch creation results.

        Arguments:
            args: Parsed command arguments
            results: List of successful creations
            errors: List of errors
        """
        if args.output == "json":
            output = {
                "success": len(results),
                "failed": len(errors),
                "issues": results,
                "errors": errors,
            }
            print(json.dumps(output, indent=2))
        else:
            print("\n📊 Batch Create Summary:")
            print(f"   ✅ Successfully created: {len(results)}")
            if errors:
                print(f"   ❌ Failed: {len(errors)}")
                for error in errors:
                    print(f"      - {Path(error['file']).name}: {error['error']}")

            if results:
                print("\n🔗 Created Issues:")
                jira_url = EnvFetcher.get("JIRA_URL")
                for result in results:
                    print(f"   {result['key']}: {result['title']}")
                    print(f"      {jira_url}/browse/{result['key']}")

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
