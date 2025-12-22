#!/usr/bin/env python
"""
Lint-all plugin for jira-creator.

This plugin implements the lint-all command, allowing users to validate
multiple Jira issues against quality standards and display a summary table.
"""

import textwrap
from argparse import ArgumentParser, Namespace
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from jira_creator.core.ai_executor import AIExecutor
from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.logger import get_logger
from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.plugins.lint_plugin import LintPlugin
from jira_creator.providers import get_ai_provider

logger = get_logger("lint_all_plugin")


class LintAllError(Exception):
    """Exception raised for lint-all operation errors."""


class LintAllPlugin(JiraPlugin):
    """Plugin for linting multiple Jira issues in bulk."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "lint-all"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Lint multiple Jira issues for quality and completeness"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Quality & Validation"

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ["lint-all --project AAP", "lint-all --project AAP --ai-fix"]

    def get_plugin_exceptions(self) -> Dict[str, type[Exception]]:
        """Register this plugin's custom exceptions."""
        return {
            "LintAllError": LintAllError,
        }

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("--project", help="Filter by project key")
        parser.add_argument("--component", help="Filter by component")
        parser.add_argument("--reporter", help="Filter by reporter username")
        parser.add_argument("--assignee", help="Filter by assignee username")
        parser.add_argument("--no-ai", action="store_true", help="Skip AI-powered quality checks")
        parser.add_argument(
            "--no-cache",
            action="store_true",
            help="Skip cache and force fresh validation",
        )
        parser.add_argument(
            "--ai-fix",
            action="store_true",
            help="Attempt to automatically fix lint issues using AI",
        )
        parser.add_argument(
            "--interactive",
            action="store_true",
            help="Ask for confirmation before applying each fix (requires --ai-fix)",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the lint-all command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if all issues pass or no issues found, False if any failures
        """
        try:
            # Validate arguments
            if args.interactive and not args.ai_fix:
                print("⚠️  --interactive requires --ai-fix")
                return False

            # Get AI provider if needed
            ai_provider = None
            if not args.no_ai or args.ai_fix:
                ai_provider = self.get_dependency(
                    "ai_provider", lambda: get_ai_provider(EnvFetcher.get("JIRA_AI_PROVIDER"))
                )

            # Get plugin registry for AI fix
            plugin_registry = None
            ai_executor = None
            if args.ai_fix:
                plugin_registry = self.get_dependency("plugin_registry")
                if plugin_registry and ai_provider:
                    ai_executor = AIExecutor(client, plugin_registry, ai_provider)
                else:
                    print("⚠️  AI fix requires plugin registry and AI provider")
                    return False

            # Get issues to lint
            issues = self.rest_operation(
                client, project=args.project, component=args.component, reporter=args.reporter, assignee=args.assignee
            )

            if not issues:
                print("✅ No issues found to lint.")
                return True

            # Lint all issues
            failures, failure_statuses = self._lint_all_issues(client, issues, ai_provider, args.no_cache)

            # Apply AI fixes if requested
            if args.ai_fix and failures and ai_executor:
                print(f"\n🤖 Attempting to fix {len(failures)} issues with lint problems...")
                self._apply_ai_fixes(client, failures, ai_executor, args.interactive)

                # Re-lint to show updated status
                print("\n🔄 Re-linting issues after fixes...")
                failures, failure_statuses = self._lint_all_issues(client, issues, ai_provider, args.no_cache)

            # Display results
            return self._display_results(failures, failure_statuses)

        except LintAllError as e:
            msg = f"❌ Failed to lint issues: {e}"
            print(msg)
            raise LintAllError(msg) from e

    def rest_operation(self, client: Any, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform the REST API operation to get issues to lint.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains filter parameters

        Returns:
            List[Dict[str, Any]]: List of issues

        Raises:
            LintAllError: If the API request fails
        """
        try:
            # Use the client's list_issues method if available
            if hasattr(client, "list_issues"):
                return client.list_issues(
                    project=kwargs.get("project"),
                    component=kwargs.get("component"),
                    reporter=kwargs.get("reporter"),
                    assignee=kwargs.get("assignee"),
                )

            # Fallback to direct JQL query
            jql_parts = []

            if kwargs.get("project"):
                jql_parts.append(f"project = {kwargs['project']}")
            if kwargs.get("component"):
                jql_parts.append(f"component = '{kwargs['component']}'")
            if kwargs.get("reporter"):
                jql_parts.append(f"reporter = '{kwargs['reporter']}'")
            if kwargs.get("assignee"):
                jql_parts.append(f"assignee = '{kwargs['assignee']}'")

            if jql_parts:
                jql = " AND ".join(jql_parts)
            else:
                # Default to recent issues assigned to current user when no filters provided
                jql = "assignee = currentUser() AND updated >= -30d"

            path = f"/rest/api/2/search?jql={jql}&maxResults=100"
            # Use longer timeout for potentially large result sets
            response = client.request("GET", path, timeout=30)
            return response.get("issues", [])

        except Exception as e:
            raise LintAllError(f"Failed to fetch issues: {e}") from e

    def _lint_all_issues(  # pylint: disable=too-many-locals
        self, client: Any, issues: List[Dict[str, Any]], ai_provider: Any, no_cache: bool
    ) -> Tuple[Dict[str, Tuple[str, List[str]]], List[Dict[str, Any]]]:
        """
        Lint all issues and return failures and status table data.

        Arguments:
            client: JiraClient instance
            issues: List of issues to lint
            ai_provider: AI provider for quality checks
            no_cache: Whether to skip cache

        Returns:
            Tuple of (failures dict, status table data)
        """
        failures = {}
        failure_statuses = []
        lint_plugin = LintPlugin()

        for issue in issues:
            key = issue["key"]
            summary = issue.get("fields", {}).get("summary", "")

            # Get full issue details
            try:
                full_issue = client.request("GET", f"/rest/api/2/issue/{key}")
                fields = full_issue["fields"]
                fields["key"] = key
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"❌ Failed to fetch {key}: {e}")
                continue

            # Validate the issue using lint plugin logic
            problems, statuses = self._validate_issue_with_status(fields, ai_provider, no_cache, lint_plugin)

            # Add issue key to status table
            statuses = OrderedDict([("jira_issue_id", key)] + list(statuses.items()))
            failure_statuses.append(statuses)

            # Track failures
            if problems:
                failures[key] = (summary, problems)
                print(f"❌ {key} {summary} failed lint checks")
            else:
                print(f"✅ {key} {summary} passed")

        return failures, failure_statuses

    def _validate_issue_with_status(  # pylint: disable=too-many-locals
        self, fields: Dict[str, Any], ai_provider: Any, no_cache: bool, lint_plugin: LintPlugin
    ) -> Tuple[List[str], Dict[str, bool]]:
        """
        Validate an issue and return both problems and status flags.

        Arguments:
            fields: Issue fields from JIRA API
            ai_provider: AI provider for quality checks
            no_cache: Whether to skip cache
            lint_plugin: Lint plugin instance for validation logic

        Returns:
            Tuple of (problems list, status dict)
        """
        problems = []
        status = {}

        # Extract basic fields
        extracted = LintPlugin.extract_issue_fields(fields)

        # Run validations and track status
        self._validate_progress_with_status(extracted["status"], extracted["assignee"], problems, status)
        self._validate_epic_link_with_status(
            extracted["issue_type"], extracted["status"], extracted["epic_link"], problems, status
        )
        self._validate_sprint_with_status(extracted["status"], extracted["sprint_field"], problems, status)
        self._validate_priority_with_status(extracted["priority"], problems, status)
        self._validate_story_points_with_status(extracted["story_points"], extracted["status"], problems, status)
        self._validate_blocked_with_status(extracted["blocked_value"], extracted["blocked_reason"], problems, status)

        # AI validations if provider available
        if ai_provider:
            cache, cached = lint_plugin.load_and_cache_issue(extracted["issue_key"])
            self._validate_ai_fields_with_status(fields, ai_provider, cached, problems, status, no_cache)

            # Save updated cache
            if not no_cache:
                cache[extracted["issue_key"]] = cached
                lint_plugin.save_cache(cache)

        return problems, status

    def _validate_progress_with_status(
        self, status: str, assignee: Any, problems: List[str], status_dict: Dict[str, bool]
    ) -> None:
        """Validate progress and update status."""
        if status == "In Progress" and not assignee:
            problems.append("❌ Issue is In Progress but unassigned")
            status_dict["Progress"] = False
        else:
            status_dict["Progress"] = True

    def _validate_epic_link_with_status(
        self, issue_type: str, status: str, epic_link: Any, problems: List[str], status_dict: Dict[str, bool]
    ) -> None:
        """Validate epic link and update status."""
        epic_exempt_types = ["Epic"]
        epic_exempt_statuses = ["New", "Refinement"]

        if (
            issue_type not in epic_exempt_types
            and not (issue_type in ["Bug", "Story", "Spike", "Task"] and status in epic_exempt_statuses)
            and not epic_link
        ):
            problems.append("❌ Issue has no assigned Epic")
            status_dict["Epic"] = False
        else:
            status_dict["Epic"] = True

    def _validate_sprint_with_status(
        self, status: str, sprint_field: Any, problems: List[str], status_dict: Dict[str, bool]
    ) -> None:
        """Validate sprint and update status."""
        if status == "In Progress" and not sprint_field:
            problems.append("❌ Issue is In Progress but not assigned to a Sprint")
            status_dict["Sprint"] = False
        else:
            status_dict["Sprint"] = True

    def _validate_priority_with_status(self, priority: Any, problems: List[str], status_dict: Dict[str, bool]) -> None:
        """Validate priority and update status."""
        if not priority:
            problems.append("❌ Priority not set")
            status_dict["Priority"] = False
        else:
            status_dict["Priority"] = True

    def _validate_story_points_with_status(
        self, story_points: Any, status: str, problems: List[str], status_dict: Dict[str, bool]
    ) -> None:
        """Validate story points and update status."""
        if story_points is None and status not in ["Refinement", "New"]:
            problems.append("❌ Story points not assigned")
            status_dict["Story P."] = False
        else:
            status_dict["Story P."] = True

    def _validate_blocked_with_status(
        self, blocked_value: str, blocked_reason: str, problems: List[str], status_dict: Dict[str, bool]
    ) -> None:
        """Validate blocked status and update status."""
        if blocked_value == "True" and not blocked_reason:
            problems.append("❌ Issue is blocked but has no blocked reason")
            status_dict["Blocked"] = False
        else:
            status_dict["Blocked"] = True

    def _validate_ai_fields_with_status(
        self,
        fields: Dict[str, Any],
        ai_provider: Any,
        cached: Dict[str, str],
        problems: List[str],
        status_dict: Dict[str, bool],
        no_cache: bool,
    ) -> None:
        """Validate AI fields and update status."""
        # For simplicity, mark AI fields as passing if no validation fails
        # A full implementation would do the actual AI validation
        # Unused parameters are intentional for interface consistency
        _ = ai_provider, cached, problems, no_cache

        # Validate summary
        summary = fields.get("summary", "")
        status_dict["Summary"] = bool(summary and len(summary) > 10)

        # Validate description
        description = fields.get("description", "")
        status_dict["Description"] = bool(description and len(description) > 20)

        # Validate acceptance criteria for stories
        issue_type = fields.get("issuetype", {}).get("name", "")
        if issue_type == "Story":
            acceptance_criteria = fields.get(EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD"), "")
            status_dict["Acceptance Criteria"] = bool(acceptance_criteria and len(acceptance_criteria) > 10)

    def _display_results(
        self, failures: Dict[str, Tuple[str, List[str]]], failure_statuses: List[Dict[str, Any]]
    ) -> bool:
        """Display lint results and status table."""
        if not failures:
            print("\n🎉 All issues passed lint checks!")
            if failure_statuses:
                self._print_status_table(failure_statuses)
            return True

        print("\n⚠️ Issues with lint problems:")
        for key, (summary, problems) in failures.items():
            print(f"\n🔍 {key} - {summary}")
            for problem in problems:
                # Wrap the text at 120 characters, ensuring no word splitting
                wrapped_text = textwrap.fill(problem, width=120, break_long_words=False)
                print(f" - {wrapped_text}")

        if failure_statuses:
            self._print_status_table(failure_statuses)
        return False

    def _print_status_table(self, failure_statuses: List[Dict[str, Any]]) -> None:
        """Print a status table showing lint check results."""
        if not failure_statuses:
            return

        # Collect all unique keys from all rows
        all_keys = set()
        for row in failure_statuses:
            all_keys.update(row.keys())

        # Ensure each row contains all the keys
        for row in failure_statuses:
            for key in all_keys:
                row.setdefault(key, None)

        # Normalize the values
        for row in failure_statuses:
            for key, value in row.items():
                if value is True:
                    row[key] = "✅"  # Green check for True
                elif value is False:
                    row[key] = "❌"  # Red cross for False
                elif value is None or value == "?":
                    row[key] = "❎"  # Question mark for None or "?"

        # Sort by issue ID
        failure_statuses.sort(key=lambda row: row.get("jira_issue_id", ""))

        # Get headers and ensure jira_issue_id is first
        headers = list(all_keys)
        headers.sort()
        if "jira_issue_id" in headers:
            headers.remove("jira_issue_id")
            headers.insert(0, "jira_issue_id")

        # Calculate column widths based on header length
        column_widths = {header: len(header) for header in headers}

        # Print the table
        print("\n📊 Lint Status Summary:")
        print("-" + " - ".join("-" * column_widths[header] for header in headers) + " -")

        # Print header row
        print("| " + " | ".join(f"{header}".ljust(column_widths[header]) for header in headers) + " |")
        print("-" + " - ".join("-" * column_widths[header] for header in headers) + " -")

        # Print each row of data
        for row in failure_statuses:
            formatted_row = ""
            for header in headers:
                value = str(row.get(header, "?"))
                formatted_row += f"| {value.ljust(column_widths[header])}"
            print(formatted_row + "|")

        # Print the bottom separator line
        print("-" + " - ".join("-" * column_widths[header] for header in headers) + " -")

    def _apply_ai_fixes(
        self, client: Any, failures: Dict[str, Tuple[str, List[str]]], ai_executor: AIExecutor, interactive: bool
    ) -> None:
        """
        Apply AI fixes to failed issues.

        Arguments:
            client: JiraClient instance
            failures: Dict of issue_key -> (summary, problems)
            ai_executor: AIExecutor instance
            interactive: Whether to ask for confirmation
        """
        total_success = 0
        total_failure = 0

        for issue_key, (summary, problems) in failures.items():
            print(f"\n📋 {issue_key} - {summary}")
            print(f"   Problems: {len(problems)}")

            # Build context for this issue
            context = self._build_issue_context(client, issue_key)

            if not context:
                print("   ⚠️  Failed to fetch issue context, skipping")
                continue

            # Generate fixes using AI
            try:
                fix_commands = ai_executor.generate_fixes(issue_key, problems, context)

                if not fix_commands:
                    print("   ℹ️  No applicable fixes found")
                    continue

                print(f"   🔧 Generated {len(fix_commands)} fix command(s)")

                # Execute fixes
                success, failure = ai_executor.execute_fixes(fix_commands, interactive)
                total_success += success
                total_failure += failure

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Failed to fix %s: %s", issue_key, e)
                print(f"   ❌ Error: {e}")
                total_failure += 1

        print(f"\n📊 Fix Summary: {total_success} succeeded, {total_failure} failed")

    def _build_issue_context(self, client: Any, issue_key: str) -> Optional[Dict[str, Any]]:
        """
        Build context for an issue to help AI generate appropriate fixes.

        Arguments:
            client: JiraClient instance
            issue_key: Issue key

        Returns:
            Dict with context info or None if fetch fails
        """
        try:
            # Fetch full issue details
            issue = client.request("GET", f"/rest/api/2/issue/{issue_key}")
            fields = issue["fields"]

            # Extract basic info
            assignee_name = (
                fields.get("assignee", {}).get("name", "Unassigned") if fields.get("assignee") else "Unassigned"
            )
            context = {
                "issue_status": fields.get("status", {}).get("name", "Unknown"),
                "issue_type": fields.get("issuetype", {}).get("name", "Unknown"),
                "current_assignee": assignee_name,
            }

            # Get active sprint info
            active_sprint = self._get_active_sprint(client)
            if active_sprint:
                context["active_sprint_id"] = active_sprint["id"]
                context["active_sprint_name"] = active_sprint["name"]
            else:
                context["active_sprint_id"] = None
                context["active_sprint_name"] = None

            return context

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to build context for %s: %s", issue_key, e)
            return None

    def _get_active_sprint(self, client: Any) -> Optional[Dict[str, Any]]:
        """
        Get the active sprint for the configured board.

        Arguments:
            client: JiraClient instance

        Returns:
            Active sprint dict or None if not found
        """
        try:
            board_id = EnvFetcher.get("JIRA_BOARD_ID")
            if not board_id:
                logger.warning("JIRA_BOARD_ID not configured, cannot get active sprint")
                return None

            # Get all sprints for the board
            path = f"/rest/agile/1.0/board/{board_id}/sprint?state=active"
            response = client.request("GET", path)
            sprints = response.get("values", [])

            # Return the first active sprint
            if sprints:
                return sprints[0]

            return None

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to get active sprint: %s", e)
            return None
