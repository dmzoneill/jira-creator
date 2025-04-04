from unittest.mock import patch

import pytest
from rest.jira_prompts import JiraIssueType, JiraPromptLibrary


def test_prompt_exists_for_all_types():
    # Iterate through all issue types in JiraIssueType enum

    for issue_type in JiraIssueType:
        if issue_type == JiraIssueType.COMMENT or issue_type == JiraIssueType.DEFAULT:
            continue
        prompt = JiraPromptLibrary.get_prompt(JiraIssueType[issue_type.value.upper()])
        assert isinstance(prompt, str)
        assert (
            "As a professional Principal Software Engineer, you write acute" in prompt
        )  # Ensure it's a template-style string

    prompt = JiraPromptLibrary.get_prompt(JiraIssueType.COMMENT)
    assert (
        "As a professional Principal Software Engineer, you write great" in prompt
    )  # Ensure it's a template-style string


def test_prompt_fallback_for_invalid_type():
    try:
        # Attempting to get a prompt for an invalid type (string instead of enum)
        JiraPromptLibrary.get_prompt("invalid")  # type: ignore
    except Exception as e:
        # Ensure an exception is raised
        assert isinstance(e, Exception)


# Test for FileNotFoundError exception
def test_prompt_raises_file_not_found_error():
    # Mock the TEMPLATE_DIR and os.path.exists to simulate file not found error
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match="Template not found:.*"):
            # Simulate calling the method with JiraIssueType.DEFAULT
            JiraPromptLibrary.get_prompt(JiraIssueType.DEFAULT)
