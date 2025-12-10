#!/usr/bin/env python
"""
Abstract base class that defines the required interface for all AI providers.

Methods:
- improve_text(self, prompt: str, text: str) -> str: This method should be implemented by each AI provider to improve
the text based on the prompt.
Arguments:
- prompt (str): The initial prompt to provide context for improving the text.
- text (str): The text to be improved.
Returns:
- str: The improved version of the text.
"""

# pylint: disable=too-few-public-methods

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """
    Abstract base class that defines the required interface for all AI providers.

    Attributes:
    - prompt (str): The initial prompt to provide context for improving the text.
    - text (str): The text to be improved.
    """

    @staticmethod
    def extract_content(text: str) -> str:
        """
        Extract content between delimiter markers (---).

        Many AI models add explanatory text before/after the actual content,
        enclosed in --- delimiters. This method extracts just the content.

        Arguments:
        - text (str): The raw AI response text

        Returns:
        - str: The extracted content, or the original text if no delimiters found
        """
        # Look for content between --- markers
        if "---" in text:
            parts = text.split("---")
            if len(parts) >= 3:
                # Return the content between first and second ---
                return parts[1].strip()
        # No delimiters found, return original (stripped)
        return text.strip()

    @abstractmethod
    def improve_text(self, prompt: str, text: str) -> str:
        """
        This method should be implemented by each AI provider to improve the text based on the prompt.

        Arguments:
        - prompt (str): The initial prompt to provide context for improving the text.
        - text (str): The text to be improved.

        Returns:
        - str: The improved version of the text.
        """

    @abstractmethod
    def analyze_error(self, prompt: str, error_context: str) -> str:
        """
        Analyze an error and suggest code-level fixes.

        This method should be implemented by each AI provider to analyze JIRA API errors
        and provide actionable suggestions for fixing them.

        Arguments:
        - prompt (str): The system prompt providing context for error analysis.
        - error_context (str): JSON-formatted error context containing request/response details.

        Returns:
        - str: Markdown-formatted analysis with root cause, proposed fix, and workarounds.
        """

    @abstractmethod
    def analyze_and_fix_error(self, prompt: str, error_context: str) -> str:
        """
        Analyze an error and return a structured fix proposal.

        This method should be implemented by each AI provider to analyze JIRA API errors
        and return a JSON-formatted fix proposal that can be automatically applied.

        Arguments:
        - prompt (str): The system prompt providing context for error analysis and fix generation.
        - error_context (str): JSON-formatted error context containing request/response details.

        Returns:
        - str: JSON-formatted fix proposal with structure:
            {
                "analysis": "Markdown analysis...",
                "fix_type": "codebase" | "payload" | "none",
                "confidence": 0.85,
                "file_changes": [
                    {
                        "file_path": "/absolute/path/to/file.py",
                        "old_content": "current code...",
                        "new_content": "fixed code...",
                        "line_start": 42,
                        "line_end": 45
                    }
                ],
                "payload_fix": {"fields": {...}},
                "reasoning": "Why this fix type was chosen"
            }
        """
