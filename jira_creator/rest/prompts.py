#!/usr/bin/env python
"""
This module provides an enumeration for various issue types used in project management, including BUG, EPIC, SPIKE,
STORY, TASK, COMMENT, DEFAULT, QC, and AIHELPER. It also contains the PromptLibrary class, which offers functionality
to retrieve file contents and generate prompts based on the specified issue type.

Classes:
- IssueType: An enumeration that defines different types of issues.
- PromptLibrary: A class that provides methods to read template files and generate prompts based on issue types.

Functions:
- get_file_contents(full_name): Reads and returns the contents of a specified template file.
- get_prompt(issue_type: IssueType) -> str: Generates a prompt message based on the provided issue type.
"""

import os
from enum import Enum


class IssueType(Enum):
    """
    This class defines different types of issues that can be used in a project management system.

    Attributes:
    - BUG (str): Represents a bug type issue.
    - EPIC (str): Represents an epic type issue.
    - SPIKE (str): Represents a spike type issue.
    - STORY (str): Represents a story type issue.
    - TASK (str): Represents a task type issue.
    - COMMENT (str): Represents a comment type issue.
    - DEFAULT (str): Represents a default type issue.
    - QC (str): Represents a QC type issue.
    - AIHELPER (str): Represents an AI helper type issue.
    - TEMPLATE_DIR (str): The directory path for templates used by the project management system.
    """

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
    """
    This class provides methods to retrieve prompt contents from template files based on different issue types.

    Attributes:
    - No attributes are defined in the class, but the class relies on the following constants and types:
    - TEMPLATE_DIR: Constant representing the directory where template files are stored.
    - IssueType: Enum representing different types of issues.

    Methods:
    - get_file_contents(full_name): Static method that reads and returns the contents of a template file specified by
    'full_name'.
    - get_prompt(issue_type: IssueType) -> str: Static method that generates a prompt message based on the provided
    'issue_type'. It combines content from multiple template files depending on the issue type and returns the final
    prompt message as a string.
    """

    @staticmethod
    def get_file_contents(full_name):
        """
        Retrieve the contents of a file specified by its full name.

        Arguments:
        - full_name (str): The full name of the file to retrieve its contents.

        Side Effects:
        - Reads the contents of the file specified by 'full_name' and stores it in the 'template' variable.
        """

        template = ""
        template_path = os.path.join(TEMPLATE_DIR, f"{full_name}.tmpl")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read().strip()

        return template

    @staticmethod
    def get_prompt(issue_type: IssueType) -> str:
        """
        Return a prompt message based on the provided issue type.

        Arguments:
        - issue_type (IssueType): An enum representing the type of the issue.

        Return:
        - str: A prompt message based on the issue type.
        """

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
        elif issue_type in list(IssueType):
            prompt = PromptLibrary.get_file_contents(
                "generic"
            ) + PromptLibrary.get_file_contents("rules")

        return prompt
