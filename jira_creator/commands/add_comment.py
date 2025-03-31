import os
import subprocess
import tempfile


def handle(jira, ai_provider, default_prompt, args):
    if args.text:
        comment = args.text
    else:
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as tmp:
            tmp.write("# Enter comment below\n")
            tmp.flush()
            subprocess.call([os.environ.get("EDITOR", "vim"), tmp.name])
            tmp.seek(0)
            comment = tmp.read()

    if not comment.strip():
        print("⚠️ No comment provided. Skipping.")
        return

    try:
        cleaned = ai_provider.improve_text(default_prompt, comment)
    except Exception as e:
        print(f"⚠️ AI cleanup failed. Using raw comment. Error: {e}")
        cleaned = comment

    try:
        jira.add_comment(args.issue_key, cleaned)
        print(f"✅ Comment added to {args.issue_key}")
    except Exception as e:
        print(f"❌ Failed to add comment: {e}")
