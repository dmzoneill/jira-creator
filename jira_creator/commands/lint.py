from commands.validate_issue import handle as validate


def handle(jira, ai_provider, args):
    try:
        issue = jira._request("GET", f"/rest/api/2/issue/{args.issue_key}")
        fields = issue["fields"]
        fields["key"] = args.issue_key

        problems = validate(fields, ai_provider)[0]

        if problems:
            print(f"⚠️ Lint issues found in {args.issue_key}:")
            for p in problems:
                print(f" - {p}")
        else:
            print(f"✅ {args.issue_key} passed all lint checks")

    except Exception as e:
        print(f"❌ Failed to lint issue {args.issue_key}: {e}")
