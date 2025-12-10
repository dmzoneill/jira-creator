#!/usr/bin/env python
"""Tests for final missing branch coverage in prompts.py."""

import os
from pathlib import Path
from unittest.mock import patch

from jira_creator.rest.prompts import IssueType, PromptLibrary


class TestPromptsFinalCoverage:
    """Tests for uncovered branch in prompts.py."""

    def test_get_prompt_exists_true_branch(self):
        """Test get_prompt when os.path.exists returns True - covers 77->82."""
        # Save original os.path.exists
        original_exists = os.path.exists

        # Create a wrapper that returns True (file exists)
        def fake_exists_true(path):
            return True

        # Replace os.path.exists temporarily
        os.path.exists = fake_exists_true

        try:
            # When os.path.exists returns True, should skip the FileNotFoundError check
            # and go directly to the return statement at line 82
            prompt = PromptLibrary.get_prompt(IssueType.EPIC)

            # Should return the epic prompt without any error
            assert "epic" in prompt.lower()

        finally:
            # Restore original
            os.path.exists = original_exists

    def test_get_prompt_exception_fallback(self):
        """Test get_prompt when template loading raises exception - covers lines 123-125."""
        # Mock Path.exists to return True but Path.open to raise an exception
        with patch.object(Path, "exists", return_value=True):
            # Mock the open call to raise an exception
            with patch("builtins.open", side_effect=PermissionError("Permission denied")):
                # Should catch the exception and fall back to hardcoded prompt
                prompt = PromptLibrary.get_prompt(IssueType.STORY)

                # Should still return a valid prompt (the hardcoded one)
                assert len(prompt) > 0
                assert "story" in prompt.lower() or "user" in prompt.lower()
