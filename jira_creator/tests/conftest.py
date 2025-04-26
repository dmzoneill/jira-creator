#!/usr/bin/env python
"""
This module contains pytest fixtures for unit testing the `JiraCLI` class and its interactions with the `JiraClient`.
These fixtures are designed to mock various components and behaviors, allowing for effective testing while isolating
tests from external dependencies and side effects.

Key fixtures include:
- `client`: A mocked instance of `JiraClient` for testing service interactions.
- `patch_subprocess_call`: Mocks the `subprocess.call` method to prevent actual command execution.
- `patch_tempfile_namedtemporaryfile`: Mocks `NamedTemporaryFile` to simulate file handling without real files.
- `cli`: A mocked instance of `JiraCLI` with overridden methods and an AI provider for testing.
- `mock_search_issues`: Mocks the `search_issues` method to return a predefined list of issues.
- `mock_cache_path`: Mocks the `get_cache_path` function to return a dummy file path for caching.
- `mock_load_cache`: Mocks the `load_cache` function to return a dummy cache for testing.
- `mock_save_cache`: Mocks the `save_cache` function to prevent actual file writing during tests.
- `mock_load_and_cache_issue`: Mocks the `load_and_cache_issue` function to return predefined cached values.

These fixtures facilitate comprehensive unit testing of the `JiraCLI` functionality while ensuring that dependencies
are isolated and real service calls are avoided.
"""

# import os
# import time

# conftest.py
from unittest.mock import MagicMock, patch

# import docker
# import psycopg2
# import requests
# from requests.exceptions import HTTPError
from rest.client import JiraClient  # pylint: disable=E0611
from rh_jira import JiraCLI

from core.env_fetcher import EnvFetcher  # isort: skip # pylint: disable=E0611

import pytest  # isort: skip

# Dummy file path and hash for testing
DUMMY_FILE_PATH = "/tmp/test_cache/ai-hashes.json"
DUMMY_HASH = "dummy_hash_value"


# @pytest.fixture(scope="module")
# def postgres_db():
#     client = docker.from_env()

#     # Define custom network name
#     network_name = "jira_network"

#     # Create the network if it does not exist
#     try:
#         client.networks.get(network_name)
#         print(f"Network {network_name} already exists.")
#     except docker.errors.NotFound:
#         print(f"Creating network {network_name}...")
#         client.networks.create(network_name)

#     postgres_container_name = "jira_postgres_db"
#     logs_path = os.path.abspath("./jira_config/postgres/logs")
#     data_path = os.path.abspath(
#         "./jira_config/postgres/data"
#     )  # Volume for persistent database data

#     try:
#         existing_postgres_container = client.containers.get(postgres_container_name)
#         print(
#             f"Stopping and removing existing PostgreSQL container: {postgres_container_name}..."
#         )
#         existing_postgres_container.stop()
#         existing_postgres_container.remove()
#     except docker.errors.NotFound:
#         print(f"No existing container named {postgres_container_name}.")

#     print("Starting PostgreSQL container...")

#     # Run the PostgreSQL container with volume mounting for persistence
#     postgres_container = client.containers.run(
#         "postgres:latest",
#         detach=True,
#         name=postgres_container_name,
#         environment={
#             "POSTGRES_USER": "jira",
#             "POSTGRES_PASSWORD": "jira",
#             "POSTGRES_DB": "jiradb",
#         },
#         ports={"5432/tcp": 5432},
#         volumes={
#             data_path: {"bind": "/var/lib/postgresql/data", "mode": "rw"},
#             logs_path: {"bind": "/var/log/postgresql", "mode": "rw"},
#         },
#         restart_policy={"Name": "always"},
#         network=network_name,  # Connect PostgreSQL container to the custom network
#     )

#     # Wait for PostgreSQL to fully start
#     max_retries = 10
#     retry_count = 0
#     postgres_up = False

#     while retry_count < max_retries and not postgres_up:
#         try:
#             postgres_container.reload()  # Update container status
#             if postgres_container.status == "running":
#                 postgres_up = True
#                 print("PostgreSQL is up.")
#         except Exception as e:
#             print(f"Error checking PostgreSQL container: {e}")

#         if not postgres_up:
#             time.sleep(10)
#             retry_count += 1

#     time.sleep(2)

#     if not postgres_up:
#         print("Error: PostgreSQL is not ready.")
#         pytest.fail("PostgreSQL container must be up and ready.")

#     # Initialize the PostgreSQL database schema for Jira
#     print("Initializing PostgreSQL database schema for Jira...")
#     try:
#         # Connect to PostgreSQL
#         conn = psycopg2.connect(
#             host="localhost", port="5432", dbname="jiradb", user="jira", password="jira"
#         )
#         conn.autocommit = True
#         cursor = conn.cursor()

#         # Check if the schema already exists
#         cursor.execute(
#             "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'project');"
#         )
#         schema_exists = cursor.fetchone()[0]

#         if not schema_exists:
#             print("Jira database schema not found, creating the schema...")
#             # Jira will automatically initialize the schema, so just ensure the database is ready
#         else:
#             print("Jira database schema already initialized.")

#         cursor.close()
#         conn.close()
#     except Exception as e:
#         print(f"Error while initializing the database schema: {e}")
#         pytest.fail(f"Failed to initialize the Jira database schema: {e}")

#     yield postgres_container  # Provide the container to the tests

#     # Cleanup: Stop and remove PostgreSQL container after tests
#     print("Stopping and removing PostgreSQL container...")
#     postgres_container.stop()
#     postgres_container.remove()


# @pytest.fixture(scope="module")
# def jira_instance(postgres_db):
#     client = docker.from_env()

#     # Define the custom network name
#     network_name = "jira_network"

#     jira_container_name = "jira_test_container"
#     config_path = os.path.abspath("./jira_config/jira/config")
#     logs_path = os.path.abspath("./jira_config/jira/logs")
#     data_path = os.path.abspath("./jira_config/jira/data")

#     try:
#         existing_jira_container = client.containers.get(jira_container_name)
#         print(
#             f"Stopping and removing existing Jira container: {jira_container_name}..."
#         )
#         existing_jira_container.stop()
#         existing_jira_container.remove()
#     except docker.errors.NotFound:
#         print(f"No existing container named {jira_container_name}.")

#     print("Starting Jira container...")

#     # Run Jira container with pre-configured database settings
#     container = client.containers.run(
#         "atlassian/jira-software:latest",
#         detach=True,
#         name=jira_container_name,
#         environment={
#             "JIRA_HOME": "/var/atlassian/application-data/jira"  # Jira home directory
#         },
#         ports={"8080/tcp": 8080},
#         volumes={
#             config_path: {"bind": "/var/atlassian/application-data/jira", "mode": "rw"},
#             logs_path: {"bind": "/var/log/jira", "mode": "rw"},
#             data_path: {"bind": "/var/lib/jira", "mode": "rw"},
#         },
#         restart_policy={"Name": "always"},
#         network=network_name,  # Connect Jira container to the custom network
#     )

#     # Wait for Jira to fully start and be available
#     max_retries = 20
#     retry_count = 0
#     jira_up = False

#     while retry_count < max_retries and not jira_up:
#         try:
#             container.reload()  # Update Jira container status
#             if container.status == "running":
#                 # Check Jira API to confirm it's ready
#                 url = "http://localhost:8080/rest/api/2/myself"
#                 response = requests.get(url)
#                 if response.status_code == 401:
#                     jira_up = True
#                     print("Jira is up and accessible.")
#                 else:
#                     print(f"Jira returned status {response.status_code}. Retrying...")
#         except Exception as e:
#             print(f"Error checking Jira container: {e}")

#         if not jira_up:
#             time.sleep(15)  # Increased sleep time
#             retry_count += 1

#     if not jira_up:
#         print("Error: Jira is not ready.")
#         pytest.fail("Jira container must be up and ready.")

#     # Generate a Personal Access Token (PAT) for Jira
#     token = None
#     try:
#         url = "http://localhost:8080/rest/auth/1/session"
#         headers = {"Content-Type": "application/json"}
#         payload = {"username": "admin", "password": "admin"}

#         # POST to create a session token (authentication)
#         response = requests.post(url, headers=headers, json=payload)
#         response.raise_for_status()
#         token = response.json()["session"]["value"]

#     except HTTPError as err:
#         print(f"Failed to generate token: {err}")
#         pytest.fail("Failed to configure Jira container with token.")

#     yield token  # Provide the token to the tests

#     # Cleanup: Stop and remove Jira container after tests
#     print("Stopping and removing Jira container...")
#     try:
#         container.reload()  # Reload to get updated status
#         if container.status in ["running", "exited"]:
#             container.stop(timeout=30)  # Increase timeout if needed
#         container.remove(force=True)  # Force remove in case of hanging
#     except docker.errors.NotFound:
#         print(f"No container named {jira_container_name} was found.")
#     except Exception as e:
#         print(f"Error stopping/removing Jira container: {e}")


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
    Apply patches to provided functions for testing purposes.

    Arguments:
    - cli: Command-line interface object.
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
