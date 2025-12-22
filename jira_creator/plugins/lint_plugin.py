#!/usr/bin/env python
"""
Lint plugin for jira-creator.

This plugin implements the lint command, allowing users to validate
individual Jira issues against quality standards using AI-powered checks.
"""

import hashlib
import json
import os
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List, Tuple

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.exceptions.exceptions import JiraClientRequestError
from jira_creator.providers import get_ai_provider


class LintError(Exception):
    """Exception raised for linting errors."""


class LintPlugin(JiraPlugin):
    """Plugin for linting individual Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "lint"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Lint a single Jira issue for quality and completeness"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Quality & Validation"

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ["lint AAP-12345", "lint AAP-12345 --fix"]

    def get_plugin_exceptions(self) -> Dict[str, type[Exception]]:
        """Register this plugin's custom exceptions."""
        return {
            "LintError": LintError,
        }

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key to lint (e.g., PROJ-123)")
        parser.add_argument("--no-ai", action="store_true", help="Skip AI-powered quality checks")
        parser.add_argument(
            "--no-cache",
            action="store_true",
            help="Skip cache and force fresh validation",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the lint command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if no lint issues found, False otherwise
        """
        try:
            # Get AI provider if needed
            ai_provider = None
            if not args.no_ai:
                ai_provider = self.get_dependency(
                    "ai_provider", lambda: get_ai_provider(EnvFetcher.get("JIRA_AI_PROVIDER"))
                )

            # Get issue details and validate
            issue_data = self.rest_operation(
                client, issue_key=args.issue_key, ai_provider=ai_provider, no_cache=args.no_cache
            )

            fields = issue_data.get("fields", {})
            fields["key"] = args.issue_key

            # Run validation
            problems = self._validate_issue(fields, ai_provider, args.no_cache)

            # Display results
            if problems:
                print(f"⚠️ Lint issues found in {args.issue_key}:")
                for problem in problems:
                    print(f" - {problem}")
                return False

            print(f"✅ {args.issue_key} passed all lint checks")
            return True

        except LintError as e:
            msg = f"❌ Failed to lint issue {args.issue_key}: {e}"
            print(msg)
            raise LintError(msg) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to get issue details.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key', 'ai_provider', 'no_cache'

        Returns:
            Dict[str, Any]: Issue data

        Raises:
            LintError: If the API request fails
        """
        issue_key = kwargs["issue_key"]
        try:
            path = f"/rest/api/2/issue/{issue_key}"
            return client.request("GET", path)
        except JiraClientRequestError as e:
            raise LintError(f"API request failed for {issue_key}: {e}") from e
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise LintError(f"Failed to fetch issue {issue_key}: {e}") from e

    def _validate_issue(  # pylint: disable=too-many-locals
        self, fields: Dict[str, Any], ai_provider: Any, no_cache: bool
    ) -> List[str]:
        """
        Validate an issue and return list of problems.

        Arguments:
            fields: Issue fields from JIRA API
            ai_provider: AI provider for quality checks
            no_cache: Whether to skip cache

        Returns:
            List[str]: List of validation problems
        """
        problems = []

        # Extract basic fields
        extracted = self.extract_issue_fields(fields)

        # Load cache for the issue if needed
        cache = {}
        cached = {}
        if not no_cache and ai_provider:
            cache, cached = self.load_and_cache_issue(extracted["issue_key"])

        # Run basic validations
        self._validate_progress(extracted["status"], extracted["assignee"], problems)
        self._validate_epic_link(extracted["issue_type"], extracted["status"], extracted["epic_link"], problems)
        self._validate_sprint(extracted["status"], extracted["sprint_field"], problems)
        self._validate_priority(extracted["priority"], problems)
        self._validate_story_points(extracted["story_points"], extracted["status"], problems)
        self._validate_blocked(extracted["blocked_value"], extracted["blocked_reason"], problems)

        # Run AI validations if provider available
        if ai_provider:
            self._validate_with_ai(fields, ai_provider, cached, problems, no_cache)

            # Save updated cache
            if not no_cache:
                cache[extracted["issue_key"]] = cached
                self.save_cache(cache)

        return problems

    @staticmethod
    def extract_issue_fields(fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract common issue fields used for validation.

        Arguments:
            fields: Issue fields from JIRA API

        Returns:
            Dict[str, Any]: Extracted field values
        """
        return {
            "issue_key": fields.get("key"),
            "status": fields.get("status", {}).get("name"),
            "assignee": fields.get("assignee"),
            "epic_link": fields.get(EnvFetcher.get("JIRA_EPIC_FIELD")),
            "sprint_field": fields.get(EnvFetcher.get("JIRA_SPRINT_FIELD")),
            "priority": fields.get("priority"),
            "story_points": fields.get(EnvFetcher.get("JIRA_STORY_POINTS_FIELD")),
            "blocked_value": fields.get(EnvFetcher.get("JIRA_BLOCKED_FIELD"), {}).get("value"),
            "blocked_reason": fields.get(EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD")),
            "issue_type": fields.get("issuetype", {}).get("name"),
        }

    def _validate_progress(self, status: str, assignee: Any, problems: List[str]) -> None:
        """Validate if the issue is assigned when it's in progress."""
        if status == "In Progress" and not assignee:
            problems.append("❌ Issue is In Progress but unassigned")

    def _validate_epic_link(self, issue_type: str, status: str, epic_link: Any, problems: List[str]) -> None:
        """Validate if an issue has an assigned epic link."""
        epic_exempt_types = ["Epic"]
        epic_exempt_statuses = ["New", "Refinement"]

        if (
            issue_type not in epic_exempt_types
            and not (issue_type in ["Bug", "Story", "Spike", "Task"] and status in epic_exempt_statuses)
            and not epic_link
        ):
            problems.append("❌ Issue has no assigned Epic")

    def _validate_sprint(self, status: str, sprint_field: Any, problems: List[str]) -> None:
        """Validate if the issue is assigned to a sprint when in progress."""
        if status == "In Progress" and not sprint_field:
            problems.append("❌ Issue is In Progress but not assigned to a Sprint")

    def _validate_priority(self, priority: Any, problems: List[str]) -> None:
        """Validate if priority is set."""
        if not priority:
            problems.append("❌ Priority not set")

    def _validate_story_points(self, story_points: Any, status: str, problems: List[str]) -> None:
        """Validate if story points are assigned, unless the status is 'Refinement' or 'New'."""
        if story_points is None and status not in ["Refinement", "New"]:
            problems.append("❌ Story points not assigned")

    def _validate_blocked(self, blocked_value: str, blocked_reason: str, problems: List[str]) -> None:
        """Validate if blocked issues have a reason."""
        if blocked_value == "True" and not blocked_reason:
            problems.append("❌ Issue is blocked but has no blocked reason")

    def _validate_with_ai(
        self, fields: Dict[str, Any], ai_provider: Any, cached: Dict[str, str], problems: List[str], no_cache: bool
    ) -> None:
        """Validate fields using AI for quality checks."""
        # Validate summary
        summary = fields.get("summary", "")
        if summary:
            summary_hash = self._sha256(summary)
            cached_hash = cached.get("summary_hash")

            if no_cache or summary_hash != cached_hash:
                self._validate_field_with_ai("Summary", summary, summary_hash, ai_provider, cached, problems)

        # Validate description
        description = fields.get("description", "")
        if description:
            description_hash = self._sha256(description)
            cached_hash = cached.get("description_hash")

            if no_cache or description_hash != cached_hash:
                self._validate_field_with_ai(
                    "Description", description, description_hash, ai_provider, cached, problems
                )

        # Validate acceptance criteria
        acceptance_criteria = fields.get(EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD"), "")
        if acceptance_criteria:
            ac_hash = self._sha256(acceptance_criteria)
            cached_hash = cached.get("acceptance_criteria_hash")

            if no_cache or ac_hash != cached_hash:
                self._validate_field_with_ai(
                    "Acceptance Criteria", acceptance_criteria, ac_hash, ai_provider, cached, problems
                )

    def _validate_field_with_ai(
        self,
        field_name: str,
        field_value: str,
        field_hash: str,
        ai_provider: Any,
        cached: Dict[str, str],
        problems: List[str],
    ) -> None:
        """Validate a field using AI provider."""
        try:
            reviewed = ai_provider.improve_text(
                f"""Check the quality of the following Jira {field_name}.
                Is it clear, concise, and informative? Respond with 'OK' if fine or explain why not.""",
                field_value,
            )

            if "ok" not in reviewed.lower():
                problems.append(f"❌ {field_name}: {reviewed.strip()}")
            else:
                # Update cache with validated hash
                cache_key = f"{field_name.lower().replace(' ', '_')}_hash"
                cached[cache_key] = field_hash

        except Exception as e:  # pylint: disable=broad-exception-caught
            problems.append(f"❌ Failed to validate {field_name} with AI: {e}")

    def _get_cache_path(self) -> str:
        """Return the path to the cache file for storing AI hashes."""
        return os.path.expanduser("~/.config/rh-issue/ai-hashes.json")

    def _sha256(self, text: str) -> str:
        """Return the SHA-256 hash of the input text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _load_cache(self) -> Dict[str, Any]:
        """Load cached data from file if it exists, otherwise return empty dict."""
        cache_path = self._get_cache_path()
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_cache(self, data: Dict[str, Any]) -> None:
        """Save data to cache file."""
        cache_path = self._get_cache_path()
        cache_dir = os.path.dirname(cache_path)

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except IOError:
            # Silently fail if we can't write to cache
            pass

    def load_and_cache_issue(self, issue_key: str) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Load cache and get the cached values for a given issue key."""
        cache = self._load_cache()
        cached = cache.get(issue_key, {})
        return cache, cached
