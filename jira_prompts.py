import os
from enum import Enum


class JiraIssueType(Enum):
    BUG = "bug"
    EPIC = "epic"
    SPIKE = "spike"
    STORY = "story"
    TASK = "task"


BASE_PROMPT = (
    "You are a professional Principal Software Engineer. You write acute, well-defined Jira {type}s with a strong focus on clarity, structure, and detail.\n"
    "If standard Jira sections are missing, add them—such as Description, Definition of Done, and Acceptance Criteria. "
    "If these sections already exist, preserve and clean up their format.\n"
    "Focus on fixing spelling errors, correcting grammatical issues, and improving sentence readability for greater clarity.\n\n"
    "Follow this structure:\n\n"
)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


class JiraPromptLibrary:
    @staticmethod
    def get_prompt(issue_type: JiraIssueType) -> str:
        template_path = os.path.join(TEMPLATE_DIR, f"{issue_type.value}.tmpl")
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read().strip()

        return BASE_PROMPT.format(type=issue_type.value) + template
