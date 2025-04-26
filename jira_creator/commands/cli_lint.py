#!/usr/bin/env python
"""
This module provides a function cli_lint that performs linting on a Jira issue using an AI provider.
It makes a request to Jira to retrieve issue details, validates the fields with the AI provider, and prints lint issues
if any.
If lint issues are found, it returns the problems; otherwise, it indicates a successful lint check.
In case of a LintError exception, it prints an error message and raises the exception.

Function cli_lint:
- Fetches an issue from Jira using the provided issue key and performs linting on the issue fields.
- Arguments:
- jira: Jira client object used to interact with the Jira API.
- ai_provider: AI provider object for performing linting operations.
- args: Command-line arguments containing the issue key.
- Exceptions:
- This function does not handle any exceptions explicitly. Any exceptions raised during Jira API requests will
propagate.
- Side Effects:
- Modifies the 'key' field in the retrieved Jira issue.
- Note: This function does not have a return value.
"""

from argparse import Namespace
from typing import Any, Dict, List

from commands.cli_validate_issue import cli_validate_issue as validate
from exceptions.exceptions import LintError
from providers.ai_provider import AIProvider
from rest.client import JiraClient


def cli_lint(jira: JiraClient, ai_provider: AIProvider, args: Namespace) -> List[str]:
    """
    Fetches an issue from Jira using the provided issue key and performs linting on the issue fields.

    Arguments:
    - jira: Jira client object used to interact with the Jira API.
    - ai_provider: AI provider object for performing linting operations.
    - args: Command-line arguments containing the issue key.

    Exceptions:
    - This function does not handle any exceptions explicitly. Any exceptions raised during Jira API requests will
    propagate.

    Side Effects:
    - Modifies the 'key' field in the retrieved Jira issue.

    Note: This function does not have a return value.
    """
    try:
        issue: Dict[str, Any] = jira.request(
            "GET", f"/rest/api/2/issue/{args.issue_key}"
        )
        fields: Dict[str, Any] = issue["fields"]
        fields["key"] = args.issue_key

        problems: List[str] = validate(fields, ai_provider)[0]

        if problems:
            print(f"⚠️ Lint issues found in {args.issue_key}:")
            for p in problems:
                print(f" - {p}")
            return problems

        print(f"✅ {args.issue_key} passed all lint checks")
        return problems
    except LintError as e:
        msg: str = f"❌ Failed to lint issue {args.issue_key}: {e}"
        print(msg)
        raise LintError(e) from e
