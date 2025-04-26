#!/usr/bin/env python
"""
This module provides functionality for managing different issue types in a project management context. It defines an
enumeration for various issue types such as BUG, EPIC, SPIKE, STORY, TASK, COMMENT, DEFAULT, QC, and AIHELPER. The
module also includes the PromptLibrary class, which offers methods to read template files and generate prompts based
on the specified issue type.

Classes:
- IssueType: An enumeration that defines the various types of issues that can be encountered in project management.
- PromptLibrary: A class that provides methods to read template files and generate prompts based on issue types.

Functions:
- get_file_contents(full_name): Reads and returns the contents of a specified template file.
- get_prompt(issue_type: IssueType) -> str: Generates a prompt message based on the provided issue type.
"""

import os
from enum import Enum
from typing import Optional


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


TEMPLATE_DIR: str = os.path.join(os.path.dirname(__file__), "../templates")


class PromptLibrary:
    @staticmethod
    def get_file_contents(full_name: str) -> str:
        template: str = ""
        template_path: str = os.path.join(TEMPLATE_DIR, f"{full_name}.tmpl")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read().strip()

        return template

    @staticmethod
    def get_prompt(issue_type: IssueType) -> str:
        prompt: str = ""
        full_name: str = issue_type.value.lower()

        if issue_type == IssueType.DEFAULT:
            prompt = (
                PromptLibrary.get_file_contents("rules")
                + PromptLibrary.get_file_contents("base").format(type=issue_type.value)
                + PromptLibrary.get_file_contents(full_name)
            )
        elif issue_type == IssueType.COMMENT:
            prompt = PromptLibrary.get_file_contents(full_name) + PromptLibrary.get_file_contents("rules")
        elif issue_type == IssueType.AIHELPER:
            prompt = PromptLibrary.get_file_contents(full_name)
        elif issue_type == IssueType.QC:
            prompt = PromptLibrary.get_file_contents(full_name)
        elif issue_type in list(IssueType):
            prompt = PromptLibrary.get_file_contents("generic") + PromptLibrary.get_file_contents("rules")

        return prompt