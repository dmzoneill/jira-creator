def cli_list_sprints(jira, args):
    try:
        board_id = jira.board_id if args.board_id else args.board_id
        response = jira.list_sprints(board_id)
        for sprint in response:
            print(f"    - {sprint}")

        print("✅ Successfully retrieved sprints")
        return response
    except Exception as e:
        msg = f"❌ Failed to retrieve sprints: {e}"
        print(msg)
        raise
