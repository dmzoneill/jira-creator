from exceptions.exceptions import SetPriorityError


def cli_set_priority(jira, args):
    """
    Set the priority of a Jira issue using the provided Jira instance and arguments.

    Arguments:
    - jira: A Jira instance used to set the priority of the issue.
    - args: An object containing the issue key and the priority to be set.

    Return:
    - True if the priority is set successfully.

    Exceptions:
    - SetPriorityError: Raised when there is an error setting the priority of the Jira issue.
    """

    try:
        jira.set_priority(args.issue_key, args.priority)
        print(f"✅ Priority set to '{args.priority}'")
        return True
    except SetPriorityError as e:
        msg = f"❌ Failed to set priority: {e}"
        print(msg)
        raise SetPriorityError(msg)
