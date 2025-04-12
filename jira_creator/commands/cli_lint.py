from commands.cli_validate_issue import cli_validate_issue as validate
from exceptions.exceptions import LintError


def cli_lint(jira, ai_provider, args):
    try:
        issue = jira._request("GET", f"/rest/api/2/issue/{args.issue_key}")
        fields = issue["fields"]
        fields["key"] = args.issue_key

        problems = validate(fields, ai_provider)[0]

        if problems:
            print(f"⚠️ Lint issues found in {args.issue_key}:")
            for p in problems:
                print(f" - {p}")
            return problems
        else:
            print(f"✅ {args.issue_key} passed all lint checks")
            return problems
    except LintError as e:
        msg = f"❌ Failed to lint issue {args.issue_key}: {e}"
        print(msg)
        raise (LintError(msg))
