"""
This script defines a function cli_quarterly_connection that builds an employee report based on JIRA issues. It
searches for issues within the last 90 days, retrieves relevant information, and processes it using a PromptLibrary. In
case of a QuarterlyConnectionError, it handles the exception and re-raises it.
"""

import time

from exceptions.exceptions import QuarterlyConnectionError
from rest.prompts import IssueType, PromptLibrary


def cli_quarterly_connection(jira, ai_provider):
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
        jql = "(created >= -90d OR resolutionDate >= -90d OR"
        jql += (
            " updated >= -90d OR comment ~ currentUser()) AND assignee = currentUser()"
        )
        issues = jira.search_issues(jql)

        if issues is None or len(issues) == 0:
            print("❌ No issues found for the given JQL.")
            return

        system_prompt = PromptLibrary.get_prompt(IssueType.QC)

        qc_input = ""
        for issue in issues:
            key = issue["key"]
            fields = issue["fields"]
            qc_input += "========================================================\n"
            summary = fields.get("summary") or ""
            description = jira.get_description(key) or ""
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
        raise QuarterlyConnectionError(e)
