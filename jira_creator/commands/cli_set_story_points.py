from exceptions.exceptions import SetStoryPointsError


def cli_set_story_points(jira, args):
    try:
        points = int(args.points)
    except ValueError:
        print("❌ Points must be an integer.")
        return

    try:
        jira.set_story_points(args.issue_key, points)
        print(f"✅ Set {points} story points on {args.issue_key}")
    except SetStoryPointsError as e:
        msg = f"❌ Failed to set story points: {e}"
        print(msg)
        raise (SetStoryPointsError(msg))
