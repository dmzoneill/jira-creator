from commands.validate_issue import handle as validate


def handle(jira, ai_provider, args):
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
            fields["key"] = issue["key"]
            summary = fields["summary"]

            # Debugging: Check if validate is being called and its type
            print(f"Debug: validate function type: {type(validate)}")
            print(f"Debug: Fields being passed to validate: {fields}")

            problems = validate(fields, ai_provider)

            # Debugging: Check what validate returns
            print(f"Debug: Problems returned by validate: {problems}")

            if problems:
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
                    print(f" - {p}")

    except Exception as e:
        print(f"❌ Failed to lint issues: {e}")
