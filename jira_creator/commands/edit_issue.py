import os
import subprocess
import tempfile

from jira.jira_prompts import JiraIssueType, JiraPromptLibrary


def handle(jira, ai_provider, default_prompt, try_cleanup_fn, args):
    try:
        original = jira.get_description(args.issue_key)
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as tmp:
            tmp.write(original or "")
            tmp.flush()
            subprocess.call([os.environ.get("EDITOR", "vim"), tmp.name])
            tmp.seek(0)
            edited = tmp.read()
    except Exception as e:
        print(f"❌ Failed to fetch/edit: {e}")
        return

    try:
        prompt = JiraPromptLibrary.get_prompt(
            JiraIssueType(jira.get_issue_type(args.issue_key).lower())
        )
    except Exception:
        prompt = default_prompt

    cleaned = edited if args.no_ai else try_cleanup_fn(ai_provider, prompt, edited)

    try:
        jira.update_description(args.issue_key, cleaned)
        print(f"✅ Updated {args.issue_key}")
    except Exception as e:
        print(f"❌ Update failed: {e}")
