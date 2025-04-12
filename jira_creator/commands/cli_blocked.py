from core.env_fetcher import EnvFetcher
from exceptions.exceptions import ListBlockedError


# /* jscpd:ignore-start */
def cli_blocked(jira, args):
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
        raise (ListBlockedError(msg))


# /* jscpd:ignore-end */
