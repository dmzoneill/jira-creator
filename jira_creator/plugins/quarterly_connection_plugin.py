#!/usr/bin/env python
"""
Quarterly connection plugin for jira-creator.

This plugin implements the quarterly-connection command, which generates
a quarterly employee report based on Jira activity.
"""

import time
from argparse import ArgumentParser, Namespace
from typing import Any

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import QuarterlyConnectionError
from jira_creator.plugins.base import JiraPlugin
from jira_creator.providers import get_ai_provider
from jira_creator.rest.prompts import IssueType, PromptLibrary


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
        # pylint: disable=too-many-locals
        try:
            print("🏗️ Building employee report")

            # Get current user
            user_response = client.request("GET", "/rest/api/2/myself")
            user = user_response.get("name") or user_response.get("accountId")
            if not user:
                print("❌ Could not get current user information")
                return False

            current_time = int(time.time() * 1000)
            ninety_days_ago = current_time - (90 * 24 * 60 * 60 * 1000)

            # Build JQL query for issues in last 90 days
            jql = (
                f"(assignee = currentUser() OR "
                f"reporter = currentUser() OR "
                f"comment ~ currentUser()) AND "
                f"updated >= {ninety_days_ago}"
            )

            # Search for issues using direct API call
            params = {"jql": jql, "maxResults": 1000}
            results = client.request("GET", "/rest/api/2/search", params=params)
            if not results or "issues" not in results:
                print("✅ No issues found for quarterly report")
                return True

            issues = results["issues"]
            print(f"📊 Found {len(issues)} issues for quarterly report")

            # Filter out CVE issues and process
            filtered_issues = []
            for issue in issues:
                summary = issue.get("fields", {}).get("summary", "")
                if "CVE" not in summary.upper():
                    filtered_issues.append(
                        {
                            "key": issue["key"],
                            "summary": summary,
                            "status": issue.get("fields", {}).get("status", {}).get("name", "Unknown"),
                            "type": issue.get("fields", {}).get("issuetype", {}).get("name", "Unknown"),
                        }
                    )

            if not filtered_issues:
                print("✅ No relevant issues found (filtered out CVE issues)")
                return True

            # Print summary
            print(f"\n📋 Quarterly Summary ({len(filtered_issues)} relevant issues):")
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

            # Try to get AI enhancement if available
            try:
                ai_provider = get_ai_provider(EnvFetcher.get("JIRA_AI_PROVIDER"))
                prompt_lib = PromptLibrary()
                prompt = prompt_lib.get_prompt(IssueType.QC)

                summary_text = f"Quarterly report: {len(filtered_issues)} issues across {len(issue_types)} types"
                enhanced_summary = ai_provider.improve_text(prompt, summary_text)
                print(f"\n🤖 AI-Enhanced Summary:\n{enhanced_summary}")

            except Exception as ai_error:  # pylint: disable=broad-exception-caught
                print(f"\n⚠️ AI enhancement unavailable: {ai_error}")

            return True

        except Exception as e:  # pylint: disable=broad-exception-caught
            raise QuarterlyConnectionError(f"Error generating quarterly report: {e}") from e
