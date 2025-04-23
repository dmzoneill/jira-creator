from exceptions.exceptions import SetStoryEpicError


def cli_set_story_epic(jira, args):
    """
    Set the epic for a story in Jira.

    Arguments:
    - jira: An instance of the Jira client.
    - args: A namespace containing the following attributes:
    - issue_key (str): The key of the story to update.
    - epic_key (str): The key of the epic to set for the story.

    Return:
    - bool: True if the epic was successfully set for the story.

    Exceptions:
    - SetStoryEpicError: Raised when there is an error setting the epic for the story.

    Side Effects:
    - Prints a success message if the epic is set successfully.
    - Prints an error message if setting the epic fails.
    """

    try:
        jira.set_story_epic(args.issue_key, args.epic_key)
        print(f"✅ Story's epic set to '{args.epic_key}'")
        return True
    except SetStoryEpicError as e:
        msg = f"❌ Failed to set epic: {e}"
        print(msg)
        raise SetStoryEpicError(msg)
