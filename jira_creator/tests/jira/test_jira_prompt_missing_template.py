import os
import pytest
from jira.jira_prompts import JiraPromptLibrary, JiraIssueType


def test_get_prompt_missing_template(monkeypatch):
    monkeypatch.setattr("os.path.exists", lambda path: False)

    with pytest.raises(FileNotFoundError) as excinfo:
        JiraPromptLibrary.get_prompt(JiraIssueType("story"))

    assert "Template not found" in str(excinfo.value)
