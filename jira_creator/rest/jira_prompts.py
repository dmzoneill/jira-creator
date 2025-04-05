import os
from enum import Enum


class JiraIssueType(Enum):
    BUG = "bug"
    EPIC = "epic"
    SPIKE = "spike"
    STORY = "story"
    TASK = "task"
    COMMENT = "comment"
    DEFAULT = "default"


JIRA_FORMATTING_ISSUES = (
    "Be concerned with jira formatting issues.  Some items to consider are: "
    "Convert '###' to 'h4.' and convert '##' to 'h3.' and convert '#' into 'h2.'\n\n'"
    "If there is a number before the hashes remove it.\n\n"
    "If you see a code block, something like ```yaml  some code here ```  convert it into "
    "{code:java}this format{code}\n\n"
    "Other formatting issues include the use of '**', e.g: **some text**.  This is"
    " meant to be text surrounded by a single '*' either side to indicate bold.\n\n"
    "If you spot other jira formatting issues, be sure to clean them up.\n\n"
)

BASE_PROMPT = (
    "You are a professional Principal Software Engineer. You write acute, "
    "well-defined Jira {type}s with a strong focus on clarity, structure, and "
    "detail.\n"
    "If standard Jira sections are missing, add them—such as Description, "
    "Definition of Done, and Acceptance Criteria. If these sections already "
    "exist, preserve and clean up their format.\n"
    "Focus on fixing spelling errors, correcting grammatical issues, and "
    "improving sentence readability for greater clarity.\n\n"
    "Follow this structure:\n\n"
)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "../templates")


class JiraPromptLibrary:
    @staticmethod
    def get_prompt(issue_type: JiraIssueType) -> str:
        # Check if the issue_type is "comment" first
        prompt = ""
        full_name = issue_type.value.lower()

        if issue_type == JiraIssueType.DEFAULT:
            template = ""
            template_path = os.path.join(TEMPLATE_DIR, f"{full_name}.tmpl")

            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Template not found: {template_path}")

            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read().strip()

            prompt = (
                JIRA_FORMATTING_ISSUES
                + BASE_PROMPT.format(type=issue_type.value)
                + template
            )

        elif issue_type == JiraIssueType.COMMENT:
            prompt = (
                "As a professional Principal Software Engineer, you write great "
                "comments on jira issues. As you are just writing comments, whilst "
                "being clear you don't need to heavily structure the messages. "
                "Improve clarity, fix grammar and spelling, and maintain structure."
            ) + JIRA_FORMATTING_ISSUES

        # Check if issue_type is one of the JiraIssueType enum members
        elif issue_type in [issue_type for issue_type in JiraIssueType]:
            prompt = (
                "As a professional Principal Software Engineer, you write acute, "
                "well-defined Jira issues with a strong focus on clear descriptions, "
                "definitions of done, acceptance criteria, and supporting details. "
                "If standard Jira sections are missing, add them. Improve clarity, "
                "fix grammar and spelling, and maintain structure."
            ) + JIRA_FORMATTING_ISSUES

        return prompt
