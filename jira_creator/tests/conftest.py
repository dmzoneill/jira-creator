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
    client = JiraClient()
    client._request = MagicMock()
    return client


# Fixture for patching subprocess.call
@pytest.fixture
def patch_subprocess_call():
    with patch(
        "commands.cli_edit_issue.subprocess.call", return_value=0
    ) as mock_subprocess:
        yield mock_subprocess


# Fixture for patching tempfile.NamedTemporaryFile
@pytest.fixture
def patch_tempfile_namedtemporaryfile():
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
    patch_subprocess_call,
    patch_tempfile_namedtemporaryfile,
):
    # Apply the patches by simply referencing the patch fixtures
    patch_subprocess_call  # Applies patch to subprocess.call
    patch_tempfile_namedtemporaryfile  # Applies patch to tempfile.NamedTemporaryFile

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
    with patch(
        "commands.cli_validate_issue.get_cache_path",
        return_value=DUMMY_FILE_PATH,
    ):
        yield DUMMY_FILE_PATH


# Mocking load_cache to return a dummy cache
@pytest.fixture
def mock_load_cache(mock_cache_path):
    with patch(
        "commands.cli_validate_issue.load_cache",
        return_value={DUMMY_HASH: {"summary_hash": "dummy_summary_hash"}},
    ):
        yield


# Mocking save_cache to prevent actual file writing
@pytest.fixture
def mock_save_cache(mock_cache_path):
    with patch("commands.cli_validate_issue.save_cache") as mock_save:
        yield mock_save


# Mocking load_and_cache_issue to return a dummy cache and cached values
@pytest.fixture
def mock_load_and_cache_issue(mock_save_cache):
    data = (
        {"AAP-mock_load_and_cache_issue": {"summary_hash": DUMMY_HASH}},
        {"summary_hash": DUMMY_HASH},
    )
    with patch("commands.cli_validate_issue.load_and_cache_issue", return_value=data):
        yield
