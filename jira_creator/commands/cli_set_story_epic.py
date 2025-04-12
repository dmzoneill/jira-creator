from exceptions.exceptions import SetStoryEpicError


def cli_set_story_epic(jira, args):
    try:
        jira.set_story_epic(args.issue_key, args.epic_key)
        print(f"✅ Story's epic set to '{args.epic_key}'")
        return True
    except SetStoryEpicError as e:
        msg = f"❌ Failed to set epic: {e}"
        print(msg)
        raise (SetStoryEpicError(msg))
