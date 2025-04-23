"""
This module contains a function to fetch and display blocked Jira issues using a CLI interface.

The 'cli_blocked' function takes two arguments: 'jira' (Jira API connection) and 'args' (CLI arguments).
It lists all issues based on the provided project, component, and user. If no issues are found, it prints a message and
returns True.
If blocked issues are found, it displays details such as key, status, assignee, reason, and summary for each blocked
issue.
In case of any errors, it catches and raises a 'ListBlockedError' with an appropriate message.

Note: The code between 'jscpd:ignore-start' and 'jscpd:ignore-end' comments is ignored by the code duplication
detection tool.
"""

from core.env_fetcher import EnvFetcher
from exceptions.exceptions import ListBlockedError


# /* jscpd:ignore-start */
def cli_blocked(jira, args):
    """
    Retrieve a list of blocked issues from Jira based on specified criteria.

    Arguments:
    - jira (JIRA): An instance of the JIRA API client.
    - args (Namespace): An object containing the following attributes:
    - project (str): The project key to filter the blocked issues.
    - component (str): The component to filter the blocked issues.
    - user (str, optional): The user to filter the blocked issues. If not provided, the current user will be used.

    Return:
    - list: A list of blocked issues retrieved based on the specified criteria.
    """

    try:
        issues = jira.list_issues(
            project=args.project,
            component=args.component,
            user=args.user or jira.get_current_user(),
        )

        if not issues:
            print("✅ No issues found.")
            return True

        blocked_issues = []
        for issue in issues:
            fields = issue["fields"]
            is_blocked = (
                fields.get(EnvFetcher.get("JIRA_BLOCKED_FIELD"), {}).get("value")
                == "True"
            )
            if is_blocked:
                blocked_issues.append(
                    {
                        "key": issue["key"],
                        "status": fields["status"]["name"],
                        "assignee": (
                            fields["assignee"]["displayName"]
                            if fields["assignee"]
                            else "Unassigned"
                        ),
                        "reason": fields.get(
                            EnvFetcher.get("JIRA_BLOCKED_REASON_FIELD"), "(no reason)"
                        ),
                        "summary": fields["summary"],
                    }
                )

        if not blocked_issues:
            print("✅ No blocked issues found.")
            return True

        print("🔒 Blocked issues:")
        print("-" * 80)
        for i in blocked_issues:
            print(f"{i['key']} [{i['status']}] — {i['assignee']}")
            print(f"  🔸 Reason: {i['reason']}")
            print(f"  📄 {i['summary']}")
            print("-" * 80)

        return blocked_issues

    except ListBlockedError as e:
        msg = f"❌ Failed to list blocked issues: {e}"
        print(msg)
        raise ListBlockedError(msg)


# /* jscpd:ignore-end */
