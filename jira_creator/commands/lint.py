from commands.validate_issue import handle as validate


def handle(jira, args):
    try:
        issue = jira._request("GET", f"/rest/api/2/issue/{args.issue_key}")
        fields = issue["fields"]

        problems = validate(fields, jira.ai_provider)

        if problems:
            print(f"⚠️ Lint issues found in {args.issue_key}:")
            for p in problems:
                print(f" - {p}")
        else:
            print(f"✅ {args.issue_key} passed all lint checks")

    except Exception as e:
        print(f"❌ Failed to lint issue {args.issue_key}: {e}")
