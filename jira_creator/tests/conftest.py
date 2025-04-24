#!/usr/bin/env python
"""
This module contains pytest fixtures for testing the JiraCLI class and its interactions with the JiraClient.

Fixtures include:
- `client`: A mocked instance of the JiraClient with a mocked request method.
- `patch_subprocess_call`: Patches the subprocess.call method to prevent actual command execution.
- `patch_tempfile_namedtemporaryfile`: Mocks the NamedTemporaryFile to simulate file handling without creating real
files.
- `cli`: A fixture that creates a mocked instance of JiraCLI, including mocked Jira methods and an AI provider.
- `mock_search_issues`: Mocks the search_issues method of the Jira client to return a predefined list of issues.
- `mock_cache_path`: Mocks the get_cache_path function to return a dummy file path for testing.
- `mock_load_cache`: Mocks the load_cache function to return a dummy cache for testing purposes.
- `mock_save_cache`: Mocks the save_cache function to prevent actual file writing during tests.
- `mock_load_and_cache_issue`: Mocks the load_and_cache_issue function to return predefined cached values.

These fixtures facilitate unit testing of the JiraCLI functionality while isolating dependencies and avoiding side
effects.
"""

# conftest.py
from unittest.mock import MagicMock, patch

from rest.client import JiraClient  # pylint: disable=E0611
from rh_jira import JiraCLI

from core.env_fetcher import EnvFetcher  # isort: skip # pylint: disable=E0611

import pytest  # isort: skip

# Dummy file path and hash for testing
DUMMY_FILE_PATH = "/tmp/test_cache/ai-hashes.json"
DUMMY_HASH = "dummy_hash_value"


@pytest.fixture
def client():
    """
    Creates a Jira client for interacting with Jira services.

    Returns:
    JiraClient: An instance of JiraClient for interacting with Jira services.
    """

    client = JiraClient()
    client.request = MagicMock()
    return client


# Fixture for patching subprocess.call
@pytest.fixture
def patch_subprocess_call():
    """
    Mocks the subprocess.call function from the commands.cli_edit_issue module.

    This function is used as a context manager to mock the subprocess.call function from the commands.cli_edit_issue
    module by returning a predefined value of 0. It is typically used in unit tests to simulate the behavior of
    subprocess.call without actually executing the command.
    """

    with patch(
        "commands.cli_edit_issue.subprocess.call", return_value=0
    ) as mock_subprocess:
        yield mock_subprocess


# Fixture for patching tempfile.NamedTemporaryFile
@pytest.fixture
def patch_tempfile_namedtemporaryfile():
    """
    Mocks the behavior of tempfile.NamedTemporaryFile for testing purposes.

    Arguments:
    No arguments.

    Return:
    Yields a MagicMock object representing a fake file with edited content and a fake file path.

    Side Effects:
    Modifies the behavior of tempfile.NamedTemporaryFile for the duration of the context manager.
    """

    with patch("commands.cli_edit_issue.tempfile.NamedTemporaryFile") as mock_tempfile:
        # Mock tempfile behavior
        fake_file = MagicMock()
        fake_file.__enter__.return_value = fake_file
        fake_file.read.return_value = "edited content"
        fake_file.name = "/tmp/file.md"  # Using a fake file path
        mock_tempfile.return_value = fake_file
        yield mock_tempfile


# Fixture for CLI object
@pytest.fixture
def cli(
    patch_subprocess_call,  # Applies patch to subprocess.call
    patch_tempfile_namedtemporaryfile,  # Applies patch to tempfile.NamedTemporaryFile
):
    """
    Apply patches to provided functions for testing purposes.

    Arguments:
    - patch_subprocess_call (fixture): Patch fixture for subprocess.call function.
    - patch_tempfile_namedtemporaryfile (fixture): Patch fixture for tempfile.NamedTemporaryFile function.
    """
    cli = JiraCLI()
    cli.jira = MagicMock()

    # Mock Jira methods
    cli.jira.get_description = MagicMock(return_value="Original description")
    cli.jira.update_description = MagicMock(return_value=True)
    cli.jira.get_issue_type = MagicMock(return_value="story")

    # Mock AI provider
    cli.ai_provider.improve_text = MagicMock(
        return_value="Cleaned and corrected content."
    )

    yield cli


# Mocking search_issues to return a list of issues
@pytest.fixture
def mock_search_issues(cli):
    """
    Mock search_issues function to return a list of mocked Jira issues.

    Arguments:
    - cli: An instance of the Jira CLI used to interact with Jira API.

    Side Effects:
    - Modifies the behavior of the search_issues method in the Jira CLI by mocking its return value to a predefined
    list of Jira issues.
    """

    # Mock search_issues to return a list of issues
    cli.jira.search_issues = MagicMock(
        return_value=[
            {
                "key": "AAP-mock_search_issues",
                "fields": {
                    "summary": "Run IQE tests in promotion pipelines",
                    "status": {"name": "In Progress"},
                    "assignee": {"displayName": "David O Neill"},
                    "priority": {"name": "Normal"},
                    EnvFetcher.get("JIRA_STORY_POINTS_FIELD"): 5,
                    EnvFetcher.get("JIRA_SPRINT_FIELD"): [
                        """com.atlassian.greenhopper.service.sprint.Sprint@5063ab17[id=70766,
                        rapidViewId=18242,state=ACTIVE,name=SaaS Sprint 2025-13,"
                        startDate=2025-03-27T12:01:00.000Z,endDate=2025-04-03T12:01:00.000Z]"""
                    ],
                },
            }
        ]
    )


# Mocking get_cache_path to return the dummy path
@pytest.fixture
def mock_cache_path():
    """
    This function mocks the cache path used in the 'cli_validate_issue' command.
    It temporarily replaces the 'get_cache_path' function with a dummy file path and yields the dummy file path.
    """

    with patch(
        "commands.cli_validate_issue.get_cache_path",
        return_value=DUMMY_FILE_PATH,
    ):
        yield DUMMY_FILE_PATH


# Mocking load_cache to return a dummy cache
@pytest.fixture
def mock_load_cache(mock_cache_path):
    """
    Mock a cache load operation for testing purposes.

    Arguments:
    - mock_cache_path (str): The path to the cache being mocked.

    Side Effects:
    - Temporarily patches the 'load_cache' function to return a dummy cache dictionary.

    Returns:
    - None
    """

    with patch(
        "commands.cli_validate_issue.load_cache",
        return_value={DUMMY_HASH: {"summary_hash": "dummy_summary_hash"}},
    ):
        yield


# Mocking save_cache to prevent actual file writing
@pytest.fixture
def mock_save_cache(mock_cache_path):
    """
    Mocks the save_cache function for testing purposes.

    Arguments:
    - mock_cache_path (str): The path to the mock cache.

    Yields:
    - mock_save: A mock object for the save_cache function.
    """

    with patch("commands.cli_validate_issue.save_cache") as mock_save:
        yield mock_save


# Mocking load_and_cache_issue to return a dummy cache and cached values
@pytest.fixture
def mock_load_and_cache_issue(mock_save_cache):
    """
    Mocks the 'load_and_cache_issue' function for testing purposes.

    Arguments:
    - mock_save_cache: A mock object used for saving cache.

    Side Effects:
    - Mocks the 'load_and_cache_issue' function using the provided 'mock_save_cache' object.
    """

    data = (
        {"AAP-mock_load_and_cache_issue": {"summary_hash": DUMMY_HASH}},
        {"summary_hash": DUMMY_HASH},
    )
    with patch("commands.cli_validate_issue.load_and_cache_issue", return_value=data):
        yield
