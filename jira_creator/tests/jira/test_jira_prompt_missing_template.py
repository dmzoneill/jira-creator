from unittest.mock import patch

import pytest
from jira.jira_prompts import JiraIssueType, JiraPromptLibrary


@patch("os.path.exists", return_value=False)
def test_get_prompt_missing_template(mock_exists):
    with pytest.raises(FileNotFoundError) as excinfo:
        JiraPromptLibrary.get_prompt(JiraIssueType("story"))

    assert "Template not found" in str(excinfo.value)
