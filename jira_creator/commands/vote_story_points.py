def handle(jira, args):
    try:
        points = int(args.points)
    except ValueError:
        print("❌ Points must be an integer.")
        return

    try:
        jira.vote_story_points(args.issue_key, points)
        print(f"✅ Voted {points} points on {args.issue_key}")
    except Exception as e:
        print(f"❌ Failed to vote on story points: {e}")
