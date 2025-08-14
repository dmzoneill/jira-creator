#!/usr/bin/env python
"""
Validate issue plugin for jira-creator.

This plugin implements the validate-issue command, allowing users to validate
Jira issues against various criteria and quality standards.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.plugins.base import JiraPlugin


class ValidateIssuePlugin(JiraPlugin):
    """Plugin for validating Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "validate-issue"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Validate a Jira issue against quality standards"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument("--no-ai", action="store_true", help="Skip AI-powered quality checks")
        parser.add_argument(
            "--no-cache",
            action="store_true",
            help="Skip cache and force fresh validation",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the validate-issue command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if validation passes
        """
        try:
            # Get issue details
            issue_data = self.rest_operation(client, issue_key=args.issue_key)
            fields = issue_data.get("fields", {})

            # Run validations
            issues = self._run_validations(fields, args.issue_key, args.no_ai, args.no_cache)

            # Display results
            if issues:
                print(f"\n❌ Validation failed for {args.issue_key}")
                print("=" * 50)
                for issue in issues:
                    print(f"  • {issue}")
                print("=" * 50)
                print(f"\n📊 Total issues: {len(issues)}")
                return False

            print(f"✅ {args.issue_key} passed all validations")
            return True

        except Exception as e:
            msg = f"❌ Failed to validate issue: {e}"
            print(msg)
            raise ValueError(msg) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to get issue details.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key'

        Returns:
            Dict[str, Any]: Issue data
        """
        issue_key = kwargs["issue_key"]
        path = f"/rest/api/2/issue/{issue_key}"
        return client.request("GET", path)

    def _run_validations(self, fields: Dict[str, Any], issue_key: str, no_ai: bool, no_cache: bool) -> List[str]:
        """Run all validation checks on the issue."""
        # pylint: disable=too-many-locals
        issues = []

        # Extract fields
        status = fields.get("status", {}).get("name", "").lower()
        assignee = fields.get("assignee")
        priority = fields.get("priority", {}).get("name")
        issue_type = fields.get("issuetype", {}).get("name", "").lower()

        # Custom fields
        epic_field = EnvFetcher.get("JIRA_EPIC_FIELD", "")
        sprint_field = EnvFetcher.get("JIRA_SPRINT_FIELD", "")
        story_points_field = EnvFetcher.get("JIRA_STORY_POINTS_FIELD", "")
        blocked_field = EnvFetcher.get("JIRA_BLOCKED_FIELD", "")
        blocked_reason_field = EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD", "")
        acceptance_criteria_field = EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD", "")

        # Basic validations
        if status == "in progress" and not assignee:
            issues.append("Issue is 'In Progress' but not assigned to anyone")

        if issue_type == "story" and epic_field and not fields.get(epic_field):
            issues.append("Story is not linked to an epic")

        if status == "in progress" and sprint_field and not fields.get(sprint_field):
            issues.append("Issue is 'In Progress' but not in a sprint")

        if not priority:
            issues.append("Issue has no priority set")

        if issue_type in ["story", "bug"] and story_points_field:
            story_points = fields.get(story_points_field)
            if status != "closed" and not story_points:
                issues.append(f"{issue_type.capitalize()} has no story points")

        if blocked_field and fields.get(blocked_field):
            blocked = fields.get(blocked_field, {})
            if blocked.get("value") == "True" or blocked.get("id") == "14656":
                reason = fields.get(blocked_reason_field)
                if not reason or not reason.strip():
                    issues.append("Issue is blocked but has no reason")

        # AI validations (if enabled)
        if not no_ai and issue_type in ["story", "bug", "task"]:
            ai_issues = self._validate_with_ai(fields, issue_key, acceptance_criteria_field, no_cache)
            issues.extend(ai_issues)

        return issues

    def _validate_with_ai(
        self,
        fields: Dict[str, Any],
        issue_key: str,  # pylint: disable=unused-argument
        acceptance_criteria_field: str,
        no_cache: bool,  # pylint: disable=unused-argument
    ) -> List[str]:
        """Validate fields using AI for quality checks."""
        issues = []

        # Get AI provider (for future use)
        # ai_provider = self.get_dependency("ai_provider", lambda: get_ai_provider(EnvFetcher.get("JIRA_AI_PROVIDER")))

        # Fields to validate with AI
        description = fields.get("description", "")
        acceptance_criteria = fields.get(acceptance_criteria_field, "") if acceptance_criteria_field else ""

        # Check description quality
        if description and len(description) < 50:
            issues.append("Description is too short (less than 50 characters)")

        # Check acceptance criteria for stories
        issue_type = fields.get("issuetype", {}).get("name", "").lower()
        if issue_type == "story" and acceptance_criteria_field:
            if not acceptance_criteria or len(acceptance_criteria) < 20:
                issues.append("Story has missing or insufficient acceptance criteria")

        # Note: Full AI validation would involve calling the AI provider
        # to check quality, but keeping this simple for the plugin version

        return issues
