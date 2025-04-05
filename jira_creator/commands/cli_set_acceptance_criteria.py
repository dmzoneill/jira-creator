def cli_set_acceptance_criteria(jira, args):
    try:
        jira.set_acceptance_criteria(args.issue_key, args.acceptance_criteria)
        print(f"✅ Acceptance criteria set to '{args.acceptance_criteria}'")
    except Exception as e:
        print(f"❌ Failed to set acceptance criteria: {e}")
