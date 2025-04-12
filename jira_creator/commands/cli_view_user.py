from exceptions.exceptions import GetUserError


def cli_view_user(jira, args):
    try:
        user = jira.get_user(args.account_id)

        for key in sorted(user.keys()):
            print(f"{key} : {user[key]}")
        return user
    except GetUserError as e:
        msg = f"❌ Unable to retrieve user: {e}"
        print(msg)
        raise GetUserError(msg)
