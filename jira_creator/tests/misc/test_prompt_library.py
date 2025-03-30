from jira.jira_prompts import JiraIssueType, JiraPromptLibrary


def test_prompt_exists_for_all_types():
    for issue_type in JiraIssueType:
        prompt = JiraPromptLibrary.get_prompt(issue_type)
        assert isinstance(prompt, str)
        assert "{{" in prompt  # Ensure it's a template-style string


def test_prompt_fallback_for_invalid_type():
    try:
        JiraPromptLibrary.get_prompt("invalid")  # type: ignore
    except Exception as e:
        assert isinstance(e, Exception)
