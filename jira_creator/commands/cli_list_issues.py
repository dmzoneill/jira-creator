import re

from core.env_fetcher import EnvFetcher
from exceptions.exceptions import ListIssuesError


# /* jscpd:ignore-start */
def cli_list_issues(jira, args):
    try:
        if args.reporter:
            issues = jira.list_issues(
                project=args.project,
                component=args.component,
                reporter=args.reporter,
            )
        else:
            issues = jira.list_issues(
                project=args.project,
                component=args.component,
                assignee=args.assignee,
            )

        if not issues:
            print("No issues found.")
            return

        rows = []
        for issue in issues:
            f = issue["fields"]
            sprints = f.get(EnvFetcher.get("JIRA_SPRINT_FIELD")) or []
            sprint = next(
                (
                    re.search(r"name=([^,]+)", s).group(1)
                    for s in sprints
                    if "state=ACTIVE" in s and "name=" in s
                ),
                "—",
            )

            if (
                args.status
                and args.status.lower()
                not in f.get("status", {}).get("name", "").lower()
            ):
                continue
            if (
                args.summary
                and args.summary.lower() not in f.get("summary", "").lower()
            ):
                continue
            if args.blocked and f.get(EnvFetcher.get("JIRA_BLOCKED_FIELD"), {}):
                continue
            if (
                args.unblocked
                and f.get(EnvFetcher.get("JIRA_BLOCKED_FIELD"), {}) is False
            ):
                continue

            rows.append(
                (
                    issue["key"],
                    f["status"]["name"],
                    f["assignee"]["displayName"] if f["assignee"] else "Unassigned",
                    f.get("priority", {}).get("name", "—"),
                    str(f.get(EnvFetcher.get("JIRA_STORY_POINTS_FIELD"), "—")),
                    sprint,
                    f["summary"],
                )
            )

        rows.sort(key=lambda r: (r[5], r[1]))

        headers = [
            "Key",
            "Status",
            "Assignee",
            "Priority",
            "Points",
            "Sprint",
            "Summary",
        ]

        # Ensure the "Summary" column width is limited to 60 characters
        max_summary_length = 60

        widths = [
            max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)
        ]

        # Ensure summary column width does not exceed the max length
        widths[6] = min(widths[6], max_summary_length)

        header_fmt = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
        print(header_fmt)
        print("-" * len(header_fmt))

        max_summary_length = 100
        truncate_length = 97

        for r in rows:
            # Convert r to a list if it is a tuple
            r = list(r)

            # Truncate the summary column if it exceeds max_summary_length
            if len(r[6]) > max_summary_length:
                r[6] = r[6][:truncate_length] + " .."

            # Print the formatted row
            print(" | ".join(val.ljust(widths[i]) for i, val in enumerate(r)))
        return issues
    except ListIssuesError as e:
        msg = f"❌ Failed to list issues: {e}"
        print(msg)
        raise (ListIssuesError(msg))


# /* jscpd:ignore-end */
