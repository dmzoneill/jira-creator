import os
import subprocess
import tempfile

from exceptions.exceptions import AddCommentError, AiError


def cli_add_comment(jira, ai_provider, comment_prompt, args):
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
        return False

    try:
        cleaned = ai_provider.improve_text(comment_prompt, comment)
    except AiError as e:
        msg = f"⚠️ AI cleanup failed. Using raw comment. Error: {e}"
        print(msg)
        raise (AiError(msg))

    try:
        jira.add_comment(args.issue_key, cleaned)
        print(f"✅ Comment added to {args.issue_key}")
        return True
    except AddCommentError as e:
        msg = f"❌ Failed to add comment: {e}"
        print(msg)
        raise (AddCommentError(msg))
