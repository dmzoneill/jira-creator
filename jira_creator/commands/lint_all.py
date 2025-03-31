from commands.validate_issue import handle as validate


def handle(jira, args):
    try:
        issues = jira.list_issues(args.project, args.component)

        if not issues:
            print("✅ No issues assigned to you.")
            return

        failures = {}

        for issue in issues:
            key = issue["key"]
            full_issue = jira._request("GET", f"/rest/api/2/issue/{key}")
            fields = full_issue["fields"]
            problems = validate(fields, jira.ai_provider)

            if problems:
                failures[key] = problems
                print(f"❌ {key} failed lint checks")
            else:
                print(f"✅ {key} passed")

        if not failures:
            print("\n🎉 All issues passed lint checks!")
        else:
            print("\n⚠️ Issues with lint problems:")
            for key, problems in failures.items():
                print(f"\n🔍 {key}")
                for p in problems:
                    print(f" - {p}")

    except Exception as e:
        print(f"❌ Failed to lint issues: {e}")
