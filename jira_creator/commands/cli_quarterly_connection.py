#!/usr/bin/env python
"""
This script defines a function cli_quarterly_connection that builds an employee report based on JIRA issues. It
searches for issues within the last 90 days, retrieves relevant information, and processes it using a PromptLibrary. In
case of a QuarterlyConnectionError, it handles the exception and re-raises it.

Functions:
- cli_quarterly_connection: Builds a quarterly employee report based on JIRA issues assigned to the current user.

Arguments:
- jira: A JIRA API client for interacting with JIRA issues.
- ai_provider: An AI provider for generating insights from the JIRA issues.

Exceptions:
- Raises exceptions if there are any issues with searching JIRA issues.

Side Effects:
- Prints "Building employee report".

Note: This function fetches JIRA issues created, resolved, updated, or commented on by the current user within the
last 90 days.
"""

import time
from typing import List, Optional

from exceptions.exceptions import QuarterlyConnectionError
from rest.client import JiraClient
from rest.prompts import IssueType, PromptLibrary

from providers.ai_provider import AIProvider


def cli_quarterly_connection(
    jira: JiraClient, ai_provider: AIProvider
) -> Optional[bool]:
    """
    Builds a quarterly employee report based on JIRA issues assigned to the current user.

    Arguments:
    - jira: A JIRA API client for interacting with JIRA issues.
    - ai_provider: An AI provider for generating insights from the JIRA issues.

    Exceptions:
    - Raises exceptions if there are any issues with searching JIRA issues.

    Side Effects:
    - Prints "Building employee report".

    Note: This function fetches JIRA issues created, resolved, updated, or commented on by the current user within the
    last 90 days.
    """

    try:
        print("Building employee report")
        jql: str = (
            "(created >= -90d OR resolutionDate >= -90d OR"
            " updated >= -90d OR comment ~ currentUser()) AND assignee = currentUser()"
        )
        issues: List[dict] = jira.search_issues(jql)

        if issues is None or len(issues) == 0:
            print("❌ No issues found for the given JQL.")
            return None

        system_prompt: str = PromptLibrary.get_prompt(IssueType.QC)

        qc_input: str = ""
        for issue in issues:
            key: str = issue["key"]
            fields: dict = issue["fields"]
            qc_input += "========================================================\n"
            summary: str = fields.get("summary") or ""
            description: str = jira.get_description(key) or ""
            print("Fetched: " + summary)
            time.sleep(2)
            if "CVE" in summary:
                print("Not adding CVE to analysis")
                continue
            qc_input += summary + "\n"
            qc_input += description + "\n"

        print(qc_input)

        print("Manager churning:")
        print(ai_provider.improve_text(system_prompt, qc_input))

        return True
    except QuarterlyConnectionError as e:
        print(e)
        raise QuarterlyConnectionError(e) from e
