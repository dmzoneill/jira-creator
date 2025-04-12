import os
from enum import Enum


class IssueType(Enum):
    BUG = "bug"
    EPIC = "epic"
    SPIKE = "spike"
    STORY = "story"
    TASK = "task"
    COMMENT = "comment"
    DEFAULT = "default"
    QC = "qc"
    AIHELPER = "aihelper"


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "../templates")


class PromptLibrary:
    @staticmethod
    def get_file_contents(full_name):
        template = ""
        template_path = os.path.join(TEMPLATE_DIR, f"{full_name}.tmpl")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read().strip()

        return template

    @staticmethod
    def get_prompt(issue_type: IssueType) -> str:
        # Check if the issue_type is "comment" first
        prompt = ""
        full_name = issue_type.value.lower()

        if issue_type == IssueType.DEFAULT:
            prompt = (
                PromptLibrary.get_file_contents("rules")
                + PromptLibrary.get_file_contents("base").format(type=issue_type.value)
                + PromptLibrary.get_file_contents(full_name)
            )
        elif issue_type == IssueType.COMMENT:
            prompt = PromptLibrary.get_file_contents(
                full_name
            ) + PromptLibrary.get_file_contents("rules")
        elif issue_type == IssueType.AIHELPER:
            prompt = PromptLibrary.get_file_contents(full_name)
        elif issue_type == IssueType.QC:
            prompt = PromptLibrary.get_file_contents(full_name)
        elif issue_type in [issue_type for issue_type in IssueType]:
            prompt = PromptLibrary.get_file_contents(
                "generic"
            ) + PromptLibrary.get_file_contents("rules")

        return prompt
