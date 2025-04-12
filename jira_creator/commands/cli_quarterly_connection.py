import time

from exceptions.exceptions import QuarterlyConnectionError
from rest.prompts import IssueType, PromptLibrary


def cli_quarterly_connection(jira, ai_provider):
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
        raise (QuarterlyConnectionError(e))
