from exceptions.exceptions import AddSprintError


def cli_add_sprint(jira, args):
    """
    Adds an issue to a sprint in Jira.

    Arguments:
    - jira (JIRA): An instance of the JIRA client.
    - args (Namespace): A namespace object containing 'issue_key' and 'sprint_name' attributes.
    - issue_key (str): The key of the issue to be added to the sprint.
    - sprint_name (str): The name of the sprint to add the issue to.

    Return:
    - bool: True if the issue was successfully added to the sprint.

    Exceptions:
    - AddSprintError: Raised when an error occurs while adding the issue to the sprint.

    Side Effects:
    - Prints a success message if the issue is added to the sprint.
    - Prints an error message and raises AddSprintError if an error occurs during the process.
    """

    try:
        jira.add_to_sprint_by_name(args.issue_key, args.sprint_name)
        print(f"✅ Added to sprint '{args.sprint_name}'")
        return True
    except AddSprintError as e:
        msg = f"❌ {e}"
        print(msg)
        raise AddSprintError(e) from e
