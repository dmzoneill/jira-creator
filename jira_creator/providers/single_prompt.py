#!/usr/bin/env python
"""Shared error-analysis calls for providers that POST one combined prompt."""

from typing import Callable


class SinglePromptCompletion:
    """Analyze and fix errors through a provider ``_generate`` completion."""

    _generate: Callable[[str, int], str]

    def analyze_error(self, prompt: str, error_context: str) -> str:
        """Analyze a JIRA API error through the provider completion endpoint."""
        full_prompt = f"{prompt}\n\nAnalyze this error:\n\n{error_context}"
        return self._generate(full_prompt, 120).strip()

    def analyze_and_fix_error(self, prompt: str, error_context: str) -> str:
        """Ask the provider for a JSON fix proposal."""
        full_prompt = f"{prompt}\n\nAnalyze this error and propose a fix:\n\n{error_context}"
        return self._generate(full_prompt, 120).strip()
