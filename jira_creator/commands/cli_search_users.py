from exceptions.exceptions import SearchUsersError


def cli_search_users(jira, args):
    try:
        users = jira.search_users(args.query)

        if not users:
            print("⚠️ No users found.")
            return False

        for user in users:
            print("🔹 User:")
            for key in sorted(user.keys()):
                print(f"  {key}: {user[key]}")
            print("")
        return users
    except SearchUsersError as e:
        msg = f"❌ Unable to search users: {e}"
        print(msg)
        raise SearchUsersError(msg)
