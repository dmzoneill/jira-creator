from exceptions.exceptions import SetAcceptanceCriteriaError


def cli_set_acceptance_criteria(jira, args):
    """
    Sets acceptance criteria for a Jira issue.

    Arguments:
    - jira (JIRA): A JIRA instance used to interact with Jira API.
    - args (Namespace): A namespace containing parsed arguments.
    - issue_key (str): The key of the Jira issue for which acceptance criteria will be set.
    - acceptance_criteria (str): The acceptance criteria to be set for the Jira issue.

    Return:
    - bool: True if acceptance criteria were successfully set.

    Exceptions:
    - SetAcceptanceCriteriaError: If an error occurs while setting acceptance criteria.

    Side Effects:
    - Modifies the acceptance criteria for the specified Jira issue.
    - Prints a success message if the acceptance criteria are set successfully.
    - Prints an error message if setting acceptance criteria fails.
    """

    try:
        jira.set_acceptance_criteria(args.issue_key, args.acceptance_criteria)
        print(f"✅ Acceptance criteria set to '{args.acceptance_criteria}'")
        return True
    except SetAcceptanceCriteriaError as e:
        msg = f"❌ Failed to set acceptance criteria: {e}"
        print(msg)
        raise SetAcceptanceCriteriaError(e) from e
