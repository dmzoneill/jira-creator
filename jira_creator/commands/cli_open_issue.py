import os
import subprocess

from exceptions.exceptions import OpenIssueError


def cli_open_issue(args):
    try:
        subprocess.Popen(
            ["xdg-open", os.getenv("JIRA_URL") + "/browse/" + args.issue_key]
        )

    except OpenIssueError as e:
        msg = f"❌ Failed to open issue {args.issue_key}: {e}"
        print(msg)
        raise (OpenIssueError(msg))
