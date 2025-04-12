from exceptions.exceptions import VoteStoryPointsError


def cli_vote_story_points(jira, args):
    try:
        points = int(args.points)
    except ValueError:
        print("❌ Points must be an integer.")
        return False

    try:
        jira.vote_story_points(args.issue_key, points)
        print(f"✅ Voted {points} points on {args.issue_key}")
        return True
    except VoteStoryPointsError as e:
        msg = f"❌ Failed to vote on story points: {e}"
        print(msg)
        raise (VoteStoryPointsError(msg))
