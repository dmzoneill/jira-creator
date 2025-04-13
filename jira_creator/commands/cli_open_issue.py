import subprocess

from core.env_fetcher import EnvFetcher
from exceptions.exceptions import OpenIssueError


def cli_open_issue(args):
    try:
        subprocess.Popen(
            ["xdg-open", EnvFetcher.get("JIRA_URL") + "/browse/" + args.issue_key]
        )
        return True
    except OpenIssueError as e:
        msg = f"❌ Failed to open issue {args.issue_key}: {e}"
        print(msg)
        raise (OpenIssueError(msg))
