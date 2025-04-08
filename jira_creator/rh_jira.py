#!/usr/bin/env python3
import os
import sys
from pathlib import Path

from core.env_fetcher import EnvFetcher
from exceptions.exceptions import DispatcherError
from providers import get_ai_provider
from rest.client import JiraClient
from rest.prompts import IssueType, PromptLibrary

from commands import (  # isort: skip
    _try_cleanup,
    cli_add_comment,
    cli_add_sprint,
    cli_assign,
    cli_block,
    cli_blocked,
    cli_change_type,
    cli_create_issue,
    cli_edit_issue,
    cli_lint,
    cli_lint_all,
    cli_list_issues,
    cli_open_issue,
    cli_migrate,
    cli_remove_sprint,
    cli_quarterly_connection,
    cli_search,
    cli_set_acceptance_criteria,
    cli_set_priority,
    cli_set_status,
    cli_set_story_epic,
    cli_set_story_points,
    cli_unassign,
    cli_unblock,
    cli_validate_issue,
    cli_view_issue,
    cli_vote_story_points,
)


class JiraCLI:
    def __init__(self):
        self.jira = JiraClient()
        # List of required Jira-related environment variables
        required_vars = [
            "JPAT",
            "AI_PROVIDER",
            "JIRA_URL",
            "PROJECT_KEY",
            "AFFECTS_VERSION",
            "COMPONENT_NAME",
            "PRIORITY",
            "AI_API_KEY",
            "JIRA_BOARD_ID",
            "JIRA_EPIC_FIELD",
            "JIRA_ACCEPTANCE_CRITERIA_FIELD",
            "JIRA_BLOCKED_FIELD",
            "JIRA_BLOCKED_REASON_FIELD",
            "JIRA_STORY_POINTS_FIELD",
            "JIRA_SPRINT_FIELD",
        ]

        EnvFetcher.fetch_all(required_vars)
        self.template_dir = Path(
            os.getenv(
                "TEMPLATE_DIR", os.path.join(os.path.dirname(__file__) + "/templates")
            )
        )
        self.ai_provider = get_ai_provider(os.getenv("AI_PROVIDER", "openai"))
        self.default_prompt = PromptLibrary.get_prompt(IssueType["DEFAULT"])
        self.comment_prompt = PromptLibrary.get_prompt(IssueType["COMMENT"])

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
        create.add_argument(
            "--lint",
            action="store_true",
            help="Run interactive linting on the description after AI cleanup",
        )

        list_issues = add("list-issues", "List assigned issues")
        list_issues.add_argument("--project")
        list_issues.add_argument("--component")
        list_issues.add_argument("--assignee", help="Filter by JIRA issues by user")
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
        list_issues.add_argument("--reporter", help="Filter by JIRA issues by user")

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
        edit.add_argument(
            "--lint",
            action="store_true",
            help="Run interactive linting on the description after AI cleanup",
        )

        set_priority = add("set-priority", "Set issue priority")
        set_priority.add_argument("issue_key")
        set_priority.add_argument("priority")

        set_story_epic = add("set-story-epic", "Set stories epic")
        set_story_epic.add_argument("issue_key")
        set_story_epic.add_argument("epic_key")

        set_status = add("set-status", "Set issue status")
        set_status.add_argument("issue_key")
        set_status.add_argument("status")

        set_acceptance_criteria = add(
            "set-acceptance-criteria", "Set issue acceptance criteria"
        )
        set_acceptance_criteria.add_argument("issue_key")
        set_acceptance_criteria.add_argument("acceptance_criteria")

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
        lint_all.add_argument("--assignee", help="Assignee filter")
        lint_all.add_argument("--reporter", help="Reporter filter")

        open_issue = add("open-issue", "Open issue in the browser")
        open_issue.add_argument("issue_key")

        view_issue = add("view-issue", "View issue in the console")
        view_issue.add_argument("issue_key")

        add("quarterly-connection", "Perform a quarterly connection report")

    def _dispatch_command(self, args):
        try:
            getattr(self, args.command.replace("-", "_"))(args)
        except AttributeError as e:
            msg = f"❌ Command failed: {e}"
            print(msg)
            raise (DispatcherError(msg))

    def open_issue(self, args):
        cli_open_issue(args)

    def view_issue(self, args):
        cli_view_issue(self.jira, args)

    def add_comment(self, args):
        cli_add_comment(self.jira, self.ai_provider, self.default_prompt, args)

    def create_issue(self, args):
        cli_create_issue(
            self.jira, self.ai_provider, self.default_prompt, self.template_dir, args
        )

    def list_issues(self, args):
        cli_list_issues(self.jira, args)

    def change_type(self, args):
        cli_change_type(self.jira, args)

    def migrate(self, args):
        cli_migrate(self.jira, args)

    def edit_issue(self, args):
        cli_edit_issue(
            self.jira, self.ai_provider, self.default_prompt, _try_cleanup, args
        )

    def _try_cleanup(self, prompt, text):
        return _try_cleanup(self.ai_provider, prompt, text)

    def unassign(self, args):
        cli_unassign(self.jira, args)

    def assign(self, args):
        cli_assign(self.jira, args)

    def set_priority(self, args):
        cli_set_priority(self.jira, args)

    def set_story_epic(self, args):
        cli_set_story_epic(self.jira, args)

    def remove_sprint(self, args):
        cli_remove_sprint(self.jira, args)

    def add_sprint(self, args):
        cli_add_sprint(self.jira, args)

    def set_status(self, args):
        cli_set_status(self.jira, args)

    def set_acceptance_criteria(self, args):
        cli_set_acceptance_criteria(self.jira, args)

    def vote_story_points(self, args):
        cli_vote_story_points(self.jira, args)

    def set_story_points(self, args):
        cli_set_story_points(self.jira, args)

    def block(self, args):
        cli_block(self.jira, args)

    def unblock(self, args):
        cli_unblock(self.jira, args)

    def validate_issue(self, fields):
        cli_validate_issue(fields, self.ai_provider)

    def lint(self, args):
        cli_lint(self.jira, self.ai_provider, args)

    def lint_all(self, args):
        cli_lint_all(self.jira, self.ai_provider, args)

    def blocked(self, args):
        cli_blocked(self.jira, args)

    def search(self, args):
        cli_search(self.jira, args)

    def quarterly_connection(self, args):
        cli_quarterly_connection(self.jira, self.ai_provider)


if __name__ == "__main__":
    JiraCLI().run()
