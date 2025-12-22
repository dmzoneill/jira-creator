#!/usr/bin/env python
"""
Quarterly connection plugin for jira-creator.

This plugin implements the quarterly-connection command, which generates
a quarterly employee report based on Jira activity.
"""

import time
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.providers import get_ai_provider
from jira_creator.rest.prompts import IssueType, PromptLibrary


class QuarterlyConnectionError(Exception):
    """Exception raised for quarterly connection errors."""


class QuarterlyConnectionPlugin(JiraPlugin):
    """Plugin for generating quarterly connection reports."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "quarterly-connection"

    @property
    def help_text(self) -> str:
        """Return the command help text."""
        return "Perform a quarterly connection report"

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Reporting"

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ["quarterly-connection --quarter Q1"]

    def get_plugin_exceptions(self) -> Dict[str, type[Exception]]:
        """Register this plugin's custom exceptions."""
        return {
            "QuarterlyConnectionError": QuarterlyConnectionError,
        }

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments with the argument parser."""
        # No additional arguments needed

    def execute(self, client: Any, args: Namespace) -> bool:
        """Execute the quarterly connection command."""
        try:
            result = self.rest_operation(client)
            return result
        except QuarterlyConnectionError as e:
            msg = f"❌ Failed to generate quarterly connection report: {e}"
            print(msg)
            raise QuarterlyConnectionError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> bool:
        """
        Perform the REST API operation to generate quarterly report.

        Arguments:
            client: JiraClient instance

        Returns:
            bool: True if successful
        """
        try:
            print("🏗️ Building employee report")

            # Fetch and filter issues
            filtered_issues = self._fetch_quarterly_issues(client)
            if not filtered_issues:
                return True

            # Display issue list
            self._display_issue_list(filtered_issues)

            # Generate report with AI or fallback to basic summary
            self._generate_report(filtered_issues)

            return True

        except Exception as e:  # pylint: disable=broad-exception-caught
            raise QuarterlyConnectionError(f"Error generating quarterly report: {e}") from e

    def _fetch_quarterly_issues(self, client: Any) -> list:
        """Fetch and filter quarterly issues."""
        # Get current user
        user_response = client.request("GET", "/rest/api/2/myself", timeout=30)
        user = user_response.get("name") or user_response.get("accountId")
        if not user:
            print("❌ Could not get current user information")
            return []

        # Build JQL for last 90 days
        current_time = int(time.time() * 1000)
        ninety_days_ago = current_time - (90 * 24 * 60 * 60 * 1000)
        jql = (
            f"(assignee = currentUser() OR "
            f"reporter = currentUser() OR "
            f"comment ~ currentUser()) AND "
            f"updated >= {ninety_days_ago}"
        )

        # Search for issues
        params = {"jql": jql, "maxResults": 1000}
        results = client.request("GET", "/rest/api/2/search", params=params, timeout=30)
        if not results or "issues" not in results:
            print("✅ No issues found for quarterly report")
            return []

        issues = results["issues"]
        print(f"📊 Found {len(issues)} issues for quarterly report")

        # Filter out CVE issues
        filtered_issues = [
            {
                "key": issue["key"],
                "summary": issue.get("fields", {}).get("summary", ""),
                "description": issue.get("fields", {}).get("description", ""),
                "status": issue.get("fields", {}).get("status", {}).get("name", "Unknown"),
                "type": issue.get("fields", {}).get("issuetype", {}).get("name", "Unknown"),
            }
            for issue in issues
            if "CVE" not in issue.get("fields", {}).get("summary", "").upper()
        ]

        if not filtered_issues:
            print("✅ No relevant issues found (filtered out CVE issues)")

        return filtered_issues

    def _display_issue_list(self, filtered_issues: list) -> None:
        """Display the list of issues in the report."""
        print(f"\n📋 Issues included in quarterly report ({len(filtered_issues)} issues):")
        print("-" * 60)
        for issue in filtered_issues:
            print(f"{issue['key']}: {issue['summary']}")
        print(f"\n📊 Generating quarterly report from {len(filtered_issues)} issues...")

    def _generate_report(self, filtered_issues: list) -> None:
        """Generate report using AI or fallback to basic summary."""
        # Build formatted issue list
        issue_list = [
            f"[{issue['key']}] {issue['summary']}"
            + (f"\nDescription: {issue['description'][:200]}..." if issue["description"] else "")
            + f"\nType: {issue['type']}, Status: {issue['status']}"
            for issue in filtered_issues
        ]

        # Try AI enhancement
        try:
            ai_provider = get_ai_provider(EnvFetcher.get("JIRA_AI_PROVIDER"))
            prompt_lib = PromptLibrary()
            prompt = prompt_lib.get_prompt(IssueType.QC)
            issues_text = "\n\n".join(issue_list)
            enhanced_summary = ai_provider.improve_text(prompt, issues_text)
            print(f"\n{enhanced_summary}")
        except Exception as ai_error:  # pylint: disable=broad-exception-caught
            self._print_basic_summary(filtered_issues, ai_error)

    def _print_basic_summary(self, filtered_issues: list, ai_error: Exception) -> None:
        """Print basic summary when AI is unavailable."""
        print(f"\n⚠️ AI enhancement unavailable: {ai_error}")
        print("\n📋 Issue Summary:")
        print("-" * 60)

        issue_types = {}
        status_counts = {}

        for issue in filtered_issues:
            issue_type = issue["type"]
            status = issue["status"]
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
            status_counts[status] = status_counts.get(status, 0) + 1
            print(f"{issue['key']}: {issue['summary'][:60]}...")

        print("\n📈 Issue Types:")
        for itype, count in sorted(issue_types.items()):
            print(f"  • {itype}: {count}")

        print("\n📊 Status Distribution:")
        for status, count in sorted(status_counts.items()):
            print(f"  • {status}: {count}")
