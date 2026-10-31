"""Tests for final missing branch coverage in prompts.py."""

from pathlib import Path
from unittest.mock import patch

from jira_creator.rest.prompts import IssueType, PromptLibrary


class TestPromptsFinalCoverage:
    """Tests for uncovered branch in prompts.py."""

    def test_get_prompt_exists_true_branch(self):
        """Test get_prompt when os.path.exists returns True - covers 77->82."""
        # With os.path.exists reporting True, get_prompt skips the FileNotFoundError check
        with patch("os.path.exists", return_value=True):
            prompt = PromptLibrary.get_prompt(IssueType.EPIC)

        # Should return the epic prompt without any error
        assert "epic" in prompt.lower()

    def test_get_prompt_exception_fallback(self):
        """Test get_prompt when template loading raises exception - covers lines 123-125."""
        # Path.exists reports True but opening the template raises
        with (
            patch.object(Path, "exists", return_value=True),
            patch("builtins.open", side_effect=PermissionError("Permission denied")),
        ):
            # Should catch the exception and fall back to hardcoded prompt
            prompt = PromptLibrary.get_prompt(IssueType.STORY)

        # Should still return a valid prompt (the hardcoded one)
        assert len(prompt) > 0
        assert "story" in prompt.lower() or "user" in prompt.lower()
