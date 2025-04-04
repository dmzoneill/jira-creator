import os
import subprocess
import tempfile

from commands.validate_issue import handle as validate
from rest.jira_prompts import JiraIssueType, JiraPromptLibrary


def handle(jira, ai_provider, default_prompt, try_cleanup_fn, args):
    try:
        print("Fetching description...")
        original = jira.get_description(args.issue_key)
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as tmp:
            tmp.write(original or "")
            tmp.flush()
            subprocess.call([os.environ.get("EDITOR", "vim"), tmp.name])
            tmp.seek(0)
            edited = tmp.read()
        print("Description fetched and editor closed.")
    except Exception as e:
        print(f"❌ Failed to fetch/edit: {e}")
        return

    try:
        print("Getting Jira prompt...")
        prompt = JiraPromptLibrary.get_prompt(
            JiraIssueType(jira.get_issue_type(args.issue_key).lower())
        )
    except Exception:
        prompt = default_prompt

    print("Prompt retrieved.")

    cleaned = edited if args.no_ai else try_cleanup_fn(ai_provider, prompt, edited)

    if args.lint:
        print("Starting linting...")
        while True:
            print(f"Current cleaned description: {cleaned}")
            fields = {"description": cleaned}
            problems = validate(fields, ai_provider)
            print(f"Validation issues: {problems}")

            description_problems = [
                p for p in problems if p.startswith("❌ Description:")
            ]
            print(f"Description problems: {description_problems}")

            if not description_problems:
                print("No issues found, breaking out of loop.")
                break

            print("\n⚠️ Description Lint Issues:")
            for p in description_problems:
                print(f" - {p}")

            print(
                "\n📝 Please provide more information given the problems stated above:"
            )
            user_answers = input("> ").strip()
            print(f"User entered: {user_answers}")

            prompt = (
                "Incorporate these additional details into the below Jira description.\n"
                f"Details to incorporate: {user_answers}\n"
                "Original description:\n"
                f"{cleaned}"
            )

            cleaned = ai_provider.improve_text(prompt, cleaned)
            print(f"Updated cleaned description: {cleaned}")

        print("\n🤖 Final description:\n")
        print(cleaned)

    try:
        print("Updating Jira description...")
        jira.update_description(args.issue_key, cleaned)
        print(f"✅ Updated {args.issue_key}")
    except Exception as e:
        print(f"❌ Update failed: {e}")
