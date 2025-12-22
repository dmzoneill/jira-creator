#!/usr/bin/env python
"""
Set acceptance criteria plugin for jira-creator.

This plugin implements the set-acceptance-criteria command, allowing users to
set the acceptance criteria for Jira issues.
"""

from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.logger import get_logger
from jira_creator.core.plugin_base import JiraPlugin
from jira_creator.core.plugin_config import FieldMapping
from jira_creator.exceptions.exceptions import AiError
from jira_creator.providers import get_ai_provider

logger = get_logger("set_acceptance_criteria")


class SetAcceptanceCriteriaError(Exception):
    """Exception raised when setting acceptance criteria fails."""


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

    @property
    def category(self) -> str:
        """Return the category for help organization."""
        return "Issue Modification"

    def get_plugin_exceptions(self) -> Dict[str, type[Exception]]:
        """Register this plugin's custom exceptions."""
        return {
            "SetAcceptanceCriteriaError": SetAcceptanceCriteriaError,
        }

    def get_ai_prompts(self) -> Dict[str, str]:
        """Register AI prompts for generating acceptance criteria."""
        return {
            "generate_acceptance_criteria": """Based on the following Jira issue, generate clear and testable \
acceptance criteria in markdown checklist format.

Issue Summary: {summary}

Issue Description:
{description}

Generate acceptance criteria as a markdown checklist (using * [ ] format). Focus on:
- Functional requirements
- User-facing behavior
- Edge cases
- Testing scenarios

Acceptance Criteria:""",
        }

    def get_field_mappings(self) -> Dict[str, FieldMapping]:
        """Register JIRA field mappings for acceptance criteria."""
        return {
            "acceptance_criteria": FieldMapping(
                env_var="JIRA_ACCEPTANCE_CRITERIA_FIELD",
                default="customfield_12316440",
                required=True,
                description="Custom field for acceptance criteria",
            ),
        }

    @property
    def example_commands(self) -> List[str]:
        """Return example commands."""
        return ['set-acceptance-criteria AAP-12345 "User can login successfully"']

    def register_arguments(self, parser: ArgumentParser) -> None:
        """Register command-specific arguments."""
        parser.add_argument("issue_key", help="The Jira issue key (e.g., PROJ-123)")
        parser.add_argument(
            "acceptance_criteria",
            nargs="*",
            help="The acceptance criteria (can be multiple words)",
        )
        parser.add_argument(
            "--ai-from-description",
            action="store_true",
            help="Generate acceptance criteria from issue description using AI",
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
        # Generate from description using AI if requested
        if args.ai_from_description:
            criteria = self._generate_from_description(client, args.issue_key)
        else:
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
                if args.ai_from_description:
                    print("\n📋 Generated Acceptance Criteria:")
                    print(criteria)
            else:
                print(f"✅ Acceptance criteria cleared for {args.issue_key}")

            return True

        except SetAcceptanceCriteriaError as e:
            msg = f"❌ Failed to set acceptance criteria: {e}"
            print(msg)
            raise SetAcceptanceCriteriaError(e) from e

    def _generate_from_description(self, client: Any, issue_key: str) -> str:
        """
        Generate acceptance criteria from issue description using AI.

        Arguments:
            client: JiraClient instance
            issue_key: The issue key

        Returns:
            str: Generated acceptance criteria

        Raises:
            SetAcceptanceCriteriaError: If generation fails
        """
        try:
            # Fetch the issue to get its description
            path = f"/rest/api/2/issue/{issue_key}"
            issue_data = client.request("GET", path)

            description = issue_data.get("fields", {}).get("description", "")
            if not description:
                raise SetAcceptanceCriteriaError(f"Issue {issue_key} has no description to generate from")

            summary = issue_data.get("fields", {}).get("summary", "")

            # Generate acceptance criteria using AI
            print("🤖 Generating acceptance criteria from description...")

            provider_name = EnvFetcher.get("JIRA_AI_PROVIDER", default="openai")
            provider = get_ai_provider(provider_name)

            # Get prompt from plugin's registered prompts
            prompts = self.get_ai_prompts()
            prompt_template = prompts.get("generate_acceptance_criteria", "")
            prompt = prompt_template.format(summary=summary, description=description)

            criteria = provider.complete(prompt)

            if not criteria or not criteria.strip():
                raise SetAcceptanceCriteriaError("AI generated empty acceptance criteria")

            return criteria.strip()

        except AiError as e:
            raise SetAcceptanceCriteriaError(f"AI generation failed: {e}") from e
        except Exception as e:
            raise SetAcceptanceCriteriaError(f"Failed to generate acceptance criteria: {e}") from e

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

    def get_fix_capabilities(self) -> List[Dict[str, Any]]:
        """Register fix capabilities for automated issue fixing."""
        return [
            {
                "method_name": "set_acceptance_criteria_from_description",
                "description": "Generate and set acceptance criteria from issue description using AI",
                "params": {"issue_key": "str - The JIRA issue key"},
                "conditions": {
                    "problem_patterns": ["acceptance criteria", "Acceptance Criteria"],
                    "required_status": ["Refinement"],
                    "required_type": ["Story"],
                },
            }
        ]

    def execute_fix(self, client: Any, method_name: str, args: Dict[str, Any]) -> bool:
        """
        Execute a fix method for automated issue fixing.

        Arguments:
            client: JiraClient instance
            method_name: The fix method to execute
            args: Arguments for the fix

        Returns:
            bool: True if fix succeeded, False otherwise
        """
        if method_name == "set_acceptance_criteria_from_description":
            # Use AI to generate criteria from description
            ns = Namespace(issue_key=args["issue_key"], acceptance_criteria=[], ai_from_description=True)
            try:
                return self.execute(client, ns)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("Auto-fix failed for %s: %s", args.get("issue_key"), e)
                return False

        return False
