#!/usr/bin/env python
"""
This script provides functionality to generate a quarterly employee report based on JIRA issues assigned to the
current user. It includes a function `cli_quarterly_connection` that retrieves JIRA issues from the last 90 days,
processes the information using an AI provider, and handles potential exceptions related to JIRA issue searches.

Functions:
- `cli_quarterly_connection`: Constructs a quarterly report by querying JIRA for issues created, resolved, updated,
or commented on by the current user within the last 90 days.

Arguments:
- `jira`: An instance of `JiraClient` for accessing JIRA issues.
- `ai_provider`: An instance of `AIProvider` for generating insights from the retrieved JIRA issues.

Exceptions:
- Raises `QuarterlyConnectionError` if there are issues with the JIRA search operation.

Side Effects:
- Outputs "Building employee report" to the console.

Note:
- The function filters out issues related to CVEs and prints the summarized report to the console.
"""

import time
from typing import List, Optional

from exceptions.exceptions import QuarterlyConnectionError
from providers.ai_provider import AIProvider
from rest.client import JiraClient
from rest.prompts import IssueType, PromptLibrary


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
