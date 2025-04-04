import re


def handle(jira, args):
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
                assignee=args.user,
            )

        if not issues:
            print("No issues found.")
            return

        rows = []
        for issue in issues:
            f = issue["fields"]
            sprints = f.get("customfield_12310940") or []
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
            if args.blocked and f.get("customfield_12316543", {}):
                continue
            if args.unblocked and f.get("customfield_12316543", {}) is False:
                continue

            rows.append(
                (
                    issue["key"],
                    f["status"]["name"],
                    f["assignee"]["displayName"] if f["assignee"] else "Unassigned",
                    f.get("priority", {}).get("name", "—"),
                    str(f.get("customfield_12310243", "—")),
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

        widths = [
            max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)
        ]

        header_fmt = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
        print(header_fmt)
        print("-" * len(header_fmt))

        for r in rows:
            print(" | ".join(val.ljust(widths[i]) for i, val in enumerate(r)))

    except Exception as e:
        print(f"❌ Failed to list issues: {e}")
