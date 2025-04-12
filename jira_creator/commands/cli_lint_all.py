import textwrap
from collections import OrderedDict

from commands.cli_validate_issue import cli_validate_issue as validate
from exceptions.exceptions import LintAllError


def print_status_table(failure_statuses):
    # Step 1: Collect all unique keys from all rows
    all_keys = set()
    for row in failure_statuses:
        all_keys.update(row.keys())

    # Step 2: Ensure each row contains all the keys
    for row in failure_statuses:
        for key in all_keys:
            row.setdefault(key, None)  # Or set it to '?' if you prefer

    # Step 3: Normalize the values in failure_statuses
    for row in failure_statuses:
        for key, value in row.items():
            # Normalize the values for the 'Progress', 'Epic', 'Sprint', etc. columns
            if value is True:
                row[key] = "✅"  # Green check for True
            elif value is False:
                row[key] = "❌"  # Red cross for False
            elif value is None or value == "?":
                row[key] = "❎"  # Question mark for None or "?"

    # Step 4: Count the number of "❌" (representing False) in each row
    failure_statuses.sort(key=lambda row: row.get("jira_issue_id", ""))

    # Step 5: Get headers and calculate column widths based on header lengths
    headers = list(all_keys)

    # Ensure the first column is always jira_issue_id, and others are sorted alphabetically
    headers.sort()  # Sort alphabetically
    if "jira_issue_id" in headers:
        headers.remove("jira_issue_id")  # Remove jira_issue_id from sorted list
        headers.insert(0, "jira_issue_id")  # Insert it at the beginning

    column_widths = {}

    # Calculate column widths based only on the header length
    for header in headers:
        column_widths[header] = len(header)

    # Step 6: Print the table
    # Print the separator line based on column widths
    print("-" + " - ".join("-" * column_widths[header] for header in headers) + " -")

    # Print header row
    print(
        "| "
        + " | ".join(f"{header}".ljust(column_widths[header]) for header in headers)
        + " |"
    )
    print("-" + " - ".join("-" * column_widths[header] for header in headers) + " -")

    # Print each row of data
    for row in failure_statuses:
        formatted_row = ""
        for header in headers:
            value = str(row.get(header, "?"))
            formatted_row += f"| {value.ljust(column_widths[header])}"

        # Print the formatted row
        print(formatted_row + "|")

    # Print the bottom separator line
    print("-" + " - ".join("-" * column_widths[header] for header in headers) + " -")


def cli_lint_all(jira, ai_provider, args):
    try:
        if args.reporter:
            issues = jira.list_issues(
                project=args.project, component=args.component, reporter=args.reporter
            )
        elif args.assignee:
            issues = jira.list_issues(
                project=args.project, component=args.component, assignee=args.assignee
            )
        else:
            issues = jira.list_issues(project=args.project, component=args.component)

        if not issues:
            print("✅ No issues assigned to you.")
            return True

        failures = {}
        failure_statuses = []

        for issue in issues:
            key = issue["key"]
            full_issue = jira._request("GET", f"/rest/api/2/issue/{key}")
            fields = full_issue["fields"]
            fields["key"] = issue["key"]
            summary = fields["summary"]

            problems, statuses = validate(fields, ai_provider)
            statuses = OrderedDict(statuses)
            statuses = OrderedDict([("jira_issue_id", key)] + list(statuses.items()))
            failure_statuses.append(statuses)

            if len(problems) > 0:
                failures[key] = (summary, problems)
                print(f"❌ {key} {summary} failed lint checks")
            else:
                print(f"✅ {key} {summary} passed")

        if not failures:
            print("\n🎉 All issues passed lint checks!")
        else:
            print("\n⚠️ Issues with lint problems:")
            for key, (summary, problems) in failures.items():
                print(f"\n🔍 {key} - {summary}")
                for p in problems:
                    # Wrap the text at 120 characters, ensuring no word splitting
                    wrapped_text = textwrap.fill(p, width=120, break_long_words=False)
                    print(f" - {wrapped_text}")

            print_status_table(failure_statuses)
        return failure_statuses
    except LintAllError as e:
        msg = f"❌ Failed to lint issues: {e}"
        print(msg)
        raise (LintAllError(msg))
