#!/usr/bin/env python3
import os
import sys
from pathlib import Path

from commands import (
    _try_cleanup,
    add_comment,
    add_sprint,
    assign,
    block,
    blocked,
    change_type,
    create_issue,
    edit_issue,
    lint,
    lint_all,
    list_issues,
    migrate,
    remove_sprint,
    search,
    set_priority,
    set_status,
    set_story_points,
    unassign,
    unblock,
    validate_issue,
    vote_story_points,
)
from jira.client import JiraClient
from jira.jira_prompts import JiraPromptLibrary
from providers import get_ai_provider


class JiraCLI:
    def __init__(self):
        self.template_dir = Path(
            os.getenv(
                "TEMPLATE_DIR", os.path.join(os.path.dirname(__file__) + "/templates")
            )
        )
        self.jira = JiraClient()
        self.ai_provider = get_ai_provider(os.getenv("AI_PROVIDER", "openai"))
        self.default_prompt = JiraPromptLibrary.get_prompt("default")
        self.comment_prompt = JiraPromptLibrary.get_prompt("comment")

    def run(self):
        import argparse

        import argcomplete

        prog_name = os.environ.get("CLI_NAME", os.path.basename(sys.argv[0]))
        parser = argparse.ArgumentParser(description="JIRA Issue Tool", prog=prog_name)
        subparsers = parser.add_subparsers(dest="command", required=True)

        self._register_subcommands(subparsers)
        argcomplete.autocomplete(parser)
        args = parser.parse_args()
        self._dispatch_command(args)

    def _register_subcommands(self, subparsers):
        def add(name, help_text, aliases=None):
            return subparsers.add_parser(name, help=help_text, aliases=aliases or [])

        create = add("create-issue", "Create a new issue")
        create.add_argument("type")
        create.add_argument("summary")
        create.add_argument("--edit", action="store_true")
        create.add_argument("--dry-run", action="store_true")

        list_issues = add("list-issues", "List assigned issues")
        list_issues.add_argument("--project")
        list_issues.add_argument("--component")
        list_issues.add_argument("--user")
        list_issues.add_argument(
            "--blocked", action="store_true", help="Show only blocked issues"
        )
        list_issues.add_argument(
            "--unblocked", action="store_true", help="Show only unblocked issues"
        )
        list_issues.add_argument("--status", help="Filter by JIRA status")
        list_issues.add_argument("--summary", help="Filter by summary text")
        list_issues.add_argument(
            "--show-reason",
            action="store_true",
            help="Show blocked reason field in listing",
        )

        search = add("search", "Search issues via JQL")
        search.add_argument("jql", help="JIRA Query Language expression")

        change_type = add("change", "Change issue type")
        change_type.add_argument("issue_key")
        change_type.add_argument("new_type")

        migrate = add("migrate", "Migrate issue to a new type")
        migrate.add_argument("issue_key")
        migrate.add_argument("new_type")

        edit = add("edit-issue", "Edit an issue's description")
        edit.add_argument("issue_key")
        edit.add_argument("--no-ai", action="store_true")

        set_priority = add("set-priority", "Set issue priority")
        set_priority.add_argument("issue_key")
        set_priority.add_argument("priority")

        set_status = add("set-status", "Set issue status")
        set_status.add_argument("issue_key")
        set_status.add_argument("status")

        add_sprint = add("add-sprint", "Add issue to sprint by name")
        add_sprint.add_argument("issue_key")
        add_sprint.add_argument("sprint_name")

        remove_sprint = add("remove-sprint", "Remove issue from its sprint")
        remove_sprint.add_argument("issue_key")

        assign = add("assign", "Assign a user to an issue")
        assign.add_argument("issue_key")
        assign.add_argument("assignee")

        unassign = add("unassign", "Unassign a user from an issue")
        unassign.add_argument("issue_key")

        comment = add("add-comment", "Add a comment to an issue")
        comment.add_argument("issue_key")
        comment.add_argument(
            "--text", help="Comment text (optional, otherwise opens $EDITOR)"
        )

        vote = add("vote-story-points", "Vote on story points")
        vote.add_argument("issue_key")
        vote.add_argument("points", help="Story point estimate (integer)")

        set_points = add("set-story-points", "Set story points directly")
        set_points.add_argument("issue_key")
        set_points.add_argument("points", help="Story point estimate (integer)")

        block = add("block", "Mark an issue as blocked")
        block.add_argument("issue_key")
        block.add_argument("reason", help="Reason the issue is blocked")

        unblock = add("unblock", "Mark an issue as unblocked")
        unblock.add_argument("issue_key")

        blocked = add("blocked", "List blocked issues")
        blocked.add_argument("--user", help="Filter by assignee (username)")
        blocked.add_argument("--project", help="Optional project key")
        blocked.add_argument("--component", help="Optional component")

        lint = add("lint", "Lint an issue for quality")
        lint.add_argument("issue_key")

        lint_all = add("lint-all", "Lint all issues assigned to you")
        lint_all.add_argument("--project", help="Project key override")
        lint_all.add_argument("--component", help="Component filter")

    def _dispatch_command(self, args):
        try:
            getattr(self, args.command.replace("-", "_"))(args)
        except Exception as e:
            print(f"❌ Command failed: {e}")

    def add_comment(self, args):
        add_comment.handle(self.jira, self.ai_provider, self.default_prompt, args)

    def create_issue(self, args):
        create_issue.handle(
            self.jira, self.ai_provider, self.default_prompt, self.template_dir, args
        )

    def list_issues(self, args):
        list_issues.handle(self.jira, args)

    def change_type(self, args):
        change_type.handle(self.jira, args)

    def migrate(self, args):
        migrate.handle(self.jira, args)

    def edit_issue(self, args):
        edit_issue.handle(
            self.jira, self.ai_provider, self.default_prompt, _try_cleanup.handle, args
        )

    def _try_cleanup(self, prompt, text):
        return _try_cleanup.handle(self.ai_provider, prompt, text)

    def unassign(self, args):
        unassign.handle(self.jira, args)

    def assign(self, args):
        assign.handle(self.jira, args)

    def set_priority(self, args):
        set_priority.handle(self.jira, args)

    def remove_sprint(self, args):
        remove_sprint.handle(self.jira, args)

    def add_sprint(self, args):
        add_sprint.handle(self.jira, args)

    def set_status(self, args):
        set_status.handle(self.jira, args)

    def vote_story_points(self, args):
        vote_story_points.handle(self.jira, args)

    def set_story_points(self, args):
        set_story_points.handle(self.jira, args)

    def block(self, args):
        block.handle(self.jira, args)

    def unblock(self, args):
        unblock.handle(self.jira, args)

    def validate_issue(self, fields):
        return validate_issue.handle(fields, self.ai_provider)

    def lint(self, args):
        lint.handle(self.jira, args)

    def lint_all(self, args):
        lint_all.handle(self.jira, args)

    def blocked(self, args):
        blocked.handle(self.jira, args)

    def search(self, args):
        search.handle(self.jira, args)


if __name__ == "__main__":
    JiraCLI().run()
