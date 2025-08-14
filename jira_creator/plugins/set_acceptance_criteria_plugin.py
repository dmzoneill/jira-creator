#!/usr/bin/env python
"""
Set acceptance criteria plugin for jira-creator.

This plugin implements the set-acceptance-criteria command, allowing users to
set the acceptance criteria for Jira issues.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import SetAcceptanceCriteriaError
from jira_creator.plugins.base import JiraPlugin


class SetAcceptanceCriteriaPlugin(JiraPlugin):
    """Plugin for setting acceptance criteria of Jira issues."""

    @property
    def command_name(self) -> str:
        """Return the command name."""
        return "set-acceptance-criteria"

    @property
    def help_text(self) -> str:
        """Return help text for the command."""
        return "Set the acceptance criteria for a Jira issue"

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument(
            "acceptance_criteria",
            nargs="*",
            help="The acceptance criteria (can be multiple words)",
        )

    def execute(self, client: Any, args: Namespace) -> bool:
        """
        Execute the set-acceptance-criteria command.

        Arguments:
            client: JiraClient instance
            args: Parsed command arguments

        Returns:
            bool: True if successful
        """
        # Join acceptance criteria words
        criteria = " ".join(args.acceptance_criteria) if args.acceptance_criteria else ""

        # Validate input
        if not criteria or not criteria.strip():
            print("⚠️  No acceptance criteria provided. Setting to empty.")
            criteria = ""

        try:
            self.rest_operation(client, issue_key=args.issue_key, acceptance_criteria=criteria)

            if criteria:
                print(f"✅ Acceptance criteria set for {args.issue_key}")
            else:
                print(f"✅ Acceptance criteria cleared for {args.issue_key}")

            return True

        except SetAcceptanceCriteriaError as e:
            msg = f"❌ Failed to set acceptance criteria: {e}"
            print(msg)
            raise SetAcceptanceCriteriaError(e) from e

    def rest_operation(self, client: Any, **kwargs) -> Dict[str, Any]:
        """
        Perform the REST API operation to set acceptance criteria.

        Arguments:
            client: JiraClient instance
            **kwargs: Contains 'issue_key' and 'acceptance_criteria'

        Returns:
            Dict[str, Any]: API response
        """
        issue_key = kwargs["issue_key"]
        criteria = kwargs["acceptance_criteria"]

        # Get acceptance criteria field from environment
        criteria_field = EnvFetcher.get("JIRA_ACCEPTANCE_CRITERIA_FIELD")

        path = f"/rest/api/2/issue/{issue_key}"
        payload = {"fields": {criteria_field: criteria}}

        return client.request("PUT", path, json_data=payload)
