"""
This file contains unit tests for the PromptLibrary class in the rest.prompts module.
It includes tests to ensure that prompts exist for all issue types defined in the IssueType enum.
There is also a test to verify that a FileNotFoundError exception is raised when a template file is not found.
Mocking is used to simulate scenarios where files are not found.
"""

from unittest.mock import patch

from rest.prompts import IssueType, PromptLibrary

import pytest  # isort: skip


def test_prompt_exists_for_all_types():
    """
    Check if a prompt exists for all types in the IssueType enum.
    """

    # Iterate through all issue types in IssueType enum

    for issue_type in IssueType:
        if issue_type == IssueType.COMMENT or issue_type == IssueType.DEFAULT:
            continue
        if issue_type == IssueType.QC:
            prompt = PromptLibrary.get_prompt(IssueType.QC)
            assert "You are a software engineering manager" in prompt
            continue
        if issue_type == IssueType.AIHELPER:
            prompt = PromptLibrary.get_prompt(IssueType.AIHELPER)
            assert "You are an intelligent assistant that converts" in prompt
            continue
        prompt = PromptLibrary.get_prompt(IssueType[issue_type.value.upper()])
        assert isinstance(prompt, str)
        assert (
            "As a professional Principal Software Engineer, you write acute" in prompt
        )  # Ensure it's a template-style string

    prompt = PromptLibrary.get_prompt(IssueType.COMMENT)
    assert (
        "As a professional Principal Software Engineer, you write great" in prompt
    )  # Ensure it's a template-style string


# Test for FileNotFoundError exception
def test_prompt_raises_file_not_found_error():
    """
    Simulates a file not found error when trying to retrieve a prompt from PromptLibrary.

    Arguments:
    No arguments.

    Exceptions:
    - FileNotFoundError: Raised when the specified template file is not found.

    Side Effects:
    - Modifies the behavior of os.path.exists to return False, simulating a file not found error.
    - Raises a FileNotFoundError with a specific message pattern when trying to retrieve a prompt.

    """

    # Mock the TEMPLATE_DIR and os.path.exists to simulate file not found error
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError, match="Template not found:.*"):
            # Simulate calling the method with IssueType.DEFAULT
            PromptLibrary.get_prompt(IssueType.DEFAULT)
